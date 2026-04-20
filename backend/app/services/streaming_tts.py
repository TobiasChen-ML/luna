import logging
import hashlib
import asyncio
from typing import AsyncIterator, Optional
from datetime import datetime

from ..core.config import get_settings
from .redis_service import RedisService
from .voice_service import VoiceService

logger = logging.getLogger(__name__)

STREAMING_TTS_CACHE_PREFIX = "stream_tts:"
COMMON_RESPONSES_CACHE_TTL = 86400 * 30

COMMON_RESPONSES = [
    "嗯...",
    "让我想想...",
    "好的",
    "明白了",
    "确实如此",
    "你说得对",
    "我懂你的意思",
    "嗯哼",
    "Oh really?",
    "I see",
    "Hmm...",
    "Let me think...",
    "That's interesting",
    "I understand",
    "Yes",
    "No",
]


class StreamingTTSService:
    def __init__(
        self,
        redis: Optional[RedisService] = None,
        voice_service: Optional[VoiceService] = None,
    ):
        self.settings = get_settings()
        self.redis = redis
        self._voice_service = voice_service
        self._text_buffer = ""
        self._min_chunk_size = 15
        self._max_chunk_size = 200
        self._buffer_timeout = 0.5

    async def _get_redis(self) -> RedisService:
        if self.redis is None:
            self.redis = RedisService()
        return self.redis

    async def _get_voice_service(self) -> VoiceService:
        if self._voice_service is None:
            self._voice_service = VoiceService()
        return self._voice_service

    def _get_cache_key(self, text: str, voice_id: str) -> str:
        text_hash = hashlib.sha256(f"{text}|{voice_id}".encode()).hexdigest()[:16]
        return f"{STREAMING_TTS_CACHE_PREFIX}{text_hash}"

    async def get_cached_audio(self, text: str, voice_id: str) -> Optional[bytes]:
        try:
            redis = await self._get_redis()
            cache_key = self._get_cache_key(text, voice_id)
            cached = await redis.get(cache_key)
            if cached:
                logger.debug(f"TTS cache hit for: {text[:30]}...")
                return cached
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}")
        return None

    async def cache_audio(self, text: str, voice_id: str, audio_data: bytes):
        try:
            redis = await self._get_redis()
            cache_key = self._get_cache_key(text, voice_id)
            await redis.set(cache_key, audio_data, ex=COMMON_RESPONSES_CACHE_TTL)
        except Exception as e:
            logger.warning(f"Cache store failed: {e}")

    async def pregenerate_common_responses(self, voice_id: str):
        logger.info(f"Pregenerating common responses for voice: {voice_id}")
        voice_service = await self._get_voice_service()
        
        for text in COMMON_RESPONSES:
            try:
                cached = await self.get_cached_audio(text, voice_id)
                if cached:
                    continue
                
                result = await voice_service.generate_tts(
                    text=text,
                    voice_id=voice_id,
                    provider="elevenlabs",
                    use_cache=False,
                )
                
                if result.get("audio_url"):
                    logger.debug(f"Pregenerated: {text}")
                    
            except Exception as e:
                logger.warning(f"Failed to pregenerate '{text}': {e}")

    async def stream_audio(
        self,
        text_stream: AsyncIterator[str],
        voice_id: str,
        provider: str = "elevenlabs",
    ) -> AsyncIterator[bytes]:
        voice_service = await self._get_voice_service()
        buffer = ""
        pending_task = None
        audio_queue = asyncio.Queue()
        done_sent = False

        async def process_chunk(text_chunk: str):
            nonlocal done_sent
            try:
                cached = await self.get_cached_audio(text_chunk, voice_id)
                if cached:
                    await audio_queue.put(("audio", cached))
                    return

                audio_data = b""
                async for chunk in voice_service.stream_tts(text_chunk, voice_id, provider):
                    audio_data += chunk
                    await audio_queue.put(("audio", chunk))

                if audio_data:
                    await self.cache_audio(text_chunk, voice_id, audio_data)

            except Exception as e:
                logger.error(f"Failed to process chunk: {e}")
            finally:
                if not done_sent:
                    done_sent = True
                    await audio_queue.put(("done", None))

        async for text_chunk in text_stream:
            buffer += text_chunk
            
            sentence_endings = ["。", "！", "？", ".", "!", "?", "\n"]
            for ending in sentence_endings:
                if ending in buffer:
                    split_idx = buffer.index(ending) + 1
                    text_to_process = buffer[:split_idx].strip()
                    buffer = buffer[split_idx:]
                    
                    if len(text_to_process) >= self._min_chunk_size:
                        if pending_task:
                            await pending_task
                        
                        pending_task = asyncio.create_task(process_chunk(text_to_process))

        if buffer.strip():
            if pending_task:
                await pending_task
            await process_chunk(buffer.strip())
        elif pending_task:
            await pending_task

        while True:
            try:
                item = await asyncio.wait_for(audio_queue.get(), timeout=2.0)
                if item[0] == "done":
                    break
                elif item[0] == "audio":
                    yield item[1]
            except asyncio.TimeoutError:
                break

    async def generate_immediate(
        self,
        text: str,
        voice_id: str,
        provider: str = "elevenlabs",
    ) -> bytes:
        cached = await self.get_cached_audio(text, voice_id)
        if cached:
            return cached

        voice_service = await self._get_voice_service()
        audio_data = b""
        
        async for chunk in voice_service.stream_tts(text, voice_id, provider):
            audio_data += chunk

        if audio_data:
            await self.cache_audio(text, voice_id, audio_data)

        return audio_data

    async def health_check(self) -> dict:
        return {
            "status": "healthy",
            "common_responses_count": len(COMMON_RESPONSES),
            "min_chunk_size": self._min_chunk_size,
            "max_chunk_size": self._max_chunk_size,
        }


streaming_tts_service = StreamingTTSService()
