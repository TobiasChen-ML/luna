import logging
import httpx
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, AsyncIterator

from ..core.config import get_settings, get_config_value
from ..core.exceptions import ProviderError
from .redis_service import RedisService
from .database_service import DatabaseService

logger = logging.getLogger(__name__)

TTS_CACHE_PREFIX = "tts_cache:"
TTS_CACHE_TTL = 86400 * 7


class VoiceService:
    def __init__(
        self,
        redis: Optional[RedisService] = None,
        db: Optional[DatabaseService] = None,
    ):
        self.settings = get_settings()
        self.redis = redis or RedisService()
        self.db = db or DatabaseService()
        self.client = httpx.AsyncClient(timeout=60.0)

    async def close(self):
        await self.client.aclose()

    def _get_tts_cache_key(self, text: str, voice_id: str, provider: str, speed: float) -> str:
        cache_input = f"{text}|{voice_id}|{provider}|{speed}"
        cache_hash = hashlib.sha256(cache_input.encode()).hexdigest()[:32]
        return f"{TTS_CACHE_PREFIX}{cache_hash}"

    async def generate_tts(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
        speed: float = 1.0,
        provider: str = "elevenlabs",
        output_format: str = "mp3",
        use_cache: bool = True,
        voice_db_id: Optional[str] = None,
    ) -> dict:
        cleaned_text = self._clean_text_for_tts(text)
        
        if voice_db_id:
            voice_config = await self._resolve_voice_from_db(voice_db_id)
            if voice_config:
                provider = voice_config.get("provider", provider)
                voice_id = voice_config.get("provider_voice_id", voice_id)
                model_id = voice_config.get("model_id", model_id)
                settings = voice_config.get("settings", {})
                if isinstance(settings, str):
                    try:
                        settings = json.loads(settings)
                    except (json.JSONDecodeError, ValueError):
                        settings = {}
                if isinstance(settings, dict) and "speed" in settings:
                    speed = float(settings["speed"])
        
        voice_id = voice_id or "default"
        
        if use_cache:
            cache_key = self._get_tts_cache_key(cleaned_text, voice_id, provider, speed)
            cached_result = await self.redis.get_json(cache_key)
            if cached_result:
                logger.debug(f"TTS cache hit: {cache_key}")
                return cached_result
        
        if provider == "elevenlabs":
            result = await self._elevenlabs_tts(
                cleaned_text,
                voice_id,
                model_id,
                speed,
                output_format,
            )
        elif provider == "dashscope":
            result = await self._dashscope_tts(cleaned_text, voice_id)
        else:
            raise ProviderError(f"Unknown TTS provider: {provider}")
        
        if use_cache and result.get("audio_url"):
            cache_key = self._get_tts_cache_key(cleaned_text, voice_id, provider, speed)
            await self.redis.set_json(cache_key, result, ex=TTS_CACHE_TTL)
            logger.debug(f"TTS cached: {cache_key}")
        
        return result

    def _clean_text_for_tts(self, text: str) -> str:
        import re
        text = re.sub(r"\[.*?\]", "", text)
        text = re.sub(r"\*.*?\*", "", text)
        text = re.sub(r"\n+", " ", text)
        text = text.strip()
        return text

    async def _resolve_voice_from_db(self, voice_db_id: str) -> Optional[dict]:
        from ..core.database import db
        try:
            row = await db.execute(
                "SELECT provider, provider_voice_id, model_id, settings FROM voices WHERE id = ? AND is_active = 1",
                (voice_db_id,),
                fetch=True
            )
            if row:
                return row
        except Exception as e:
            logger.warning(f"Failed to resolve voice from DB: {e}")
        return None

    async def _elevenlabs_tts(
        self,
        text: str,
        voice_id: Optional[str],
        model_id: Optional[str],
        speed: float,
        output_format: str,
    ) -> dict:
        voice_id = voice_id or "default"
        model_id = model_id or "eleven_multilingual_v2"
        
        el_base_url = await get_config_value("ELEVENLABS_BASE_URL", self.settings.elevenlabs_base_url)
        el_api_key = await get_config_value("ELEVENLABS_API_KEY", self.settings.elevenlabs_api_key)
        response = await self.client.post(
            f"{el_base_url}/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": el_api_key,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": model_id,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "speed": speed,
                },
            },
        )
        
        if response.status_code != 200:
            raise ProviderError(f"ElevenLabs API error: {response.text}")
        
        audio_data = response.content
        
        audio_url = await self._store_audio(audio_data, output_format)
        
        duration = len(audio_data) / 22050
        
        return {
            "audio_url": audio_url,
            "duration": duration,
            "voice_id": voice_id,
            "provider": "elevenlabs",
        }

    async def _dashscope_tts(self, text: str, voice_id: Optional[str]) -> dict:
        voice_id = voice_id or "zhixiaoxia"
        
        return {
            "audio_url": "",
            "duration": 0,
            "voice_id": voice_id,
            "provider": "dashscope",
        }

    async def _store_audio(self, audio_data: bytes, format: str) -> str:
        import uuid
        filename = f"{uuid.uuid4().hex}.{format}"
        return f"https://storage.example.com/audio/{filename}"

    async def generate_voice_token(
        self,
        session_id: str,
        user_id: str,
        character_id: Optional[str] = None,
        room_name: Optional[str] = None,
    ) -> dict:
        import uuid
        from ..core.config import settings
        
        if not room_name:
            room_name = f"voice_{uuid.uuid4().hex[:12]}"
        
        livekit_api_key = await get_config_value("LIVEKIT_API_KEY", settings.livekit_api_key)
        livekit_api_secret = await get_config_value("LIVEKIT_API_SECRET", settings.livekit_api_secret)
        livekit_ws_url = await get_config_value("LIVEKIT_WS_URL", settings.livekit_ws_url)
        
        if livekit_api_key and livekit_api_secret:
            try:
                from livekit import api as livekit_api
                
                token = livekit_api.AccessToken(livekit_api_key, livekit_api_secret)
                token.with_identity(user_id)
                token.with_name(f"user_{user_id}")
                token.with_grants(
                    livekit_api.VideoGrants(
                        room_join=True,
                        room=room_name,
                        can_publish=True,
                        can_subscribe=True,
                        can_publish_data=True,
                    )
                )
                
                jwt_token = token.to_jwt()
                expires_at = datetime.utcnow() + timedelta(hours=24)
                
                await self.redis.set_json(
                    f"voice_token:{room_name}",
                    {
                        "session_id": session_id,
                        "user_id": user_id,
                        "character_id": character_id,
                        "room_name": room_name,
                        "created_at": datetime.utcnow().isoformat(),
                    },
                    ex=86400,
                )
                
                return {
                    "token": jwt_token,
                    "room_name": room_name,
                    "room": room_name,
                    "livekit_url": livekit_ws_url,
                    "server_url": livekit_ws_url,
                    "url": livekit_ws_url,
                    "expires_at": expires_at.isoformat(),
                    "session_id": session_id,
                }
            except ImportError:
                logger.warning("livekit-server-sdk not installed, using fallback token")
            except Exception as e:
                logger.error(f"Failed to generate LiveKit token: {e}")
        
        import secrets
        fallback_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        await self.redis.set_json(
            f"voice_token:{room_name}",
            {
                "session_id": session_id,
                "user_id": user_id,
                "character_id": character_id,
                "room_name": room_name,
                "created_at": datetime.utcnow().isoformat(),
            },
            ex=86400,
        )
        
        return {
            "token": fallback_token,
            "room_name": room_name,
            "room": room_name,
            "expires_at": expires_at.isoformat(),
            "session_id": session_id,
        }

    async def validate_voice_token(self, token: str) -> Optional[dict]:
        cached = await self.redis.get_json(f"voice_token:{token}")
        return cached

    async def generate_voice_note(
        self,
        message_id: str,
        character_id: str,
        text: str,
        voice_id: Optional[str] = None,
    ) -> dict:
        result = await self.generate_tts(
            text=text,
            voice_id=voice_id,
            provider="elevenlabs",
        )
        
        await self.redis.set_json(
            f"voice_note:{message_id}",
            {
                "audio_url": result["audio_url"],
                "duration": result["duration"],
                "character_id": character_id,
            },
        )
        
        return {
            "message_id": message_id,
            "audio_url": result["audio_url"],
            "duration": result["duration"],
        }

    async def get_message_audio(self, message_id: str) -> Optional[dict]:
        cached = await self.redis.get_json(f"voice_note:{message_id}")
        return cached

    async def stream_tts(
        self,
        text: str,
        voice_id: str,
        provider: str = "elevenlabs",
    ) -> AsyncIterator[bytes]:
        cleaned_text = self._clean_text_for_tts(text)
        
        if provider == "elevenlabs":
            el_base_url = await get_config_value("ELEVENLABS_BASE_URL", self.settings.elevenlabs_base_url)
            el_api_key = await get_config_value("ELEVENLABS_API_KEY", self.settings.elevenlabs_api_key)
            async with self.client.stream(
                "POST",
                f"{el_base_url}/text-to-speech/{voice_id}/stream",
                headers={
                    "xi-api-key": el_api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "text": cleaned_text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                    },
                },
            ) as response:
                if response.status_code != 200:
                    raise ProviderError(f"ElevenLabs stream error: {await response.aread()}")
                
                async for chunk in response.aiter_bytes():
                    yield chunk
        else:
            raise ProviderError(f"Streaming not supported for provider: {provider}")

    async def health_check(self) -> dict:
        return {
            "status": "healthy",
            "providers": ["elevenlabs", "dashscope"],
        }