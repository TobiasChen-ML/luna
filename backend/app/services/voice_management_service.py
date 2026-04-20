import logging
import uuid
import json
import httpx
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import text

from app.core.database import db
from app.core.config import get_settings, get_config_value
from app.services.voice_service import VoiceService

logger = logging.getLogger(__name__)


class VoiceManagementService:
    def __init__(self):
        self.settings = get_settings()
        self.voice_service = VoiceService()
    
    async def list_voices(
        self,
        provider: Optional[str] = None,
        language: Optional[str] = None,
        gender: Optional[str] = None,
        tone: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        conditions = []
        params = []
        
        if provider:
            conditions.append("provider = ?")
            params.append(provider)
        if language:
            conditions.append("language = ?")
            params.append(language)
        if gender:
            conditions.append("gender = ?")
            params.append(gender)
        if tone:
            conditions.append("tone = ?")
            params.append(tone)
        if is_active is not None:
            conditions.append("is_active = ?")
            params.append(1 if is_active else 0)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        offset = (page - 1) * page_size
        
        count_query = f"SELECT COUNT(*) as total FROM voices {where_clause}"
        count_result = await db.execute(count_query, tuple(params), fetch=True)
        total = count_result["total"] if count_result else 0
        
        list_query = f"""
            SELECT * FROM voices 
            {where_clause}
            ORDER BY usage_count DESC, name ASC
            LIMIT ? OFFSET ?
        """
        params.extend([page_size, offset])
        
        rows = await db.execute(list_query, tuple(params), fetch_all=True)
        
        voices = []
        for row in rows:
            voice_dict = dict(row) if row else {}
            if voice_dict.get("settings"):
                try:
                    voice_dict["settings"] = json.loads(voice_dict["settings"])
                except (json.JSONDecodeError, ValueError):
                    voice_dict["settings"] = {}
            voices.append(voice_dict)
        
        return {
            "voices": voices,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
        }
    
    async def get_voice(self, voice_id: str) -> Optional[Dict[str, Any]]:
        result = await db.execute(
            "SELECT * FROM voices WHERE id = ?",
            (voice_id,),
            fetch=True
        )
        
        if result:
            if result.get("settings"):
                try:
                    result["settings"] = json.loads(result["settings"])
                except (json.JSONDecodeError, ValueError):
                    result["settings"] = {}
            return result
        return None
    
    async def create_voice(self, data: Dict[str, Any]) -> Dict[str, Any]:
        voice_id = data.get("id") or f"voice_{uuid.uuid4().hex[:12]}"
        
        settings = data.get("settings", {})
        if isinstance(settings, dict):
            settings = json.dumps(settings)
        
        now = datetime.utcnow().isoformat()
        
        await db.execute(
            """
            INSERT INTO voices (
                id, name, display_name, description, preview_url,
                provider, provider_voice_id, model_id, language, gender,
                tone, settings, is_active, usage_count, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (
                voice_id,
                data.get("name", ""),
                data.get("display_name"),
                data.get("description"),
                data.get("preview_url"),
                data.get("provider", "elevenlabs"),
                data.get("provider_voice_id", ""),
                data.get("model_id"),
                data.get("language", "en"),
                data.get("gender", "female"),
                data.get("tone"),
                settings,
                1 if data.get("is_active", True) else 0,
                now,
                now,
            )
        )
        
        return await self.get_voice(voice_id)
    
    async def update_voice(self, voice_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        existing = await self.get_voice(voice_id)
        if not existing:
            return None
        
        updates = []
        params = []
        
        for field in ["name", "display_name", "description", "preview_url", 
                      "provider", "provider_voice_id", "model_id", "language", 
                      "gender", "tone", "is_active"]:
            if field in data:
                updates.append(f"{field} = ?")
                if field == "is_active":
                    params.append(1 if data[field] else 0)
                else:
                    params.append(data[field])
        
        if "settings" in data:
            updates.append("settings = ?")
            settings = data["settings"]
            if isinstance(settings, dict):
                params.append(json.dumps(settings))
            else:
                params.append(settings)
        
        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        
        params.append(voice_id)
        
        query = f"UPDATE voices SET {', '.join(updates)} WHERE id = ?"
        await db.execute(query, tuple(params))
        
        return await self.get_voice(voice_id)
    
    async def delete_voice(self, voice_id: str) -> bool:
        existing = await self.get_voice(voice_id)
        if not existing:
            return False
        
        chars_result = await db.execute(
            "SELECT COUNT(*) as count FROM characters WHERE voice_id = ?",
            (voice_id,),
            fetch=True
        )
        if chars_result and chars_result.get("count", 0) > 0:
            logger.warning(f"Voice {voice_id} is used by {chars_result['count']} characters, cannot delete")
            return False
        
        await db.execute("DELETE FROM voices WHERE id = ?", (voice_id,))
        return True
    
    async def soft_delete_voice(self, voice_id: str) -> bool:
        existing = await self.get_voice(voice_id)
        if not existing:
            return False
        
        await db.execute(
            "UPDATE voices SET is_active = 0, updated_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), voice_id)
        )
        return True
    
    async def increment_usage(self, voice_id: str) -> None:
        await db.execute(
            """
            UPDATE voices SET 
                usage_count = usage_count + 1,
                last_used_at = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), voice_id)
        )
    
    async def generate_preview(self, voice_id: str, text: Optional[str] = None) -> Dict[str, Any]:
        voice = await self.get_voice(voice_id)
        if not voice:
            raise ValueError(f"Voice not found: {voice_id}")
        
        preview_text = text or self._get_preview_text(voice.get("language", "en"))
        
        settings = voice.get("settings", {})
        speed = settings.get("speed", 1.0) if isinstance(settings, dict) else 1.0
        
        result = await self.voice_service.generate_tts(
            text=preview_text,
            voice_id=voice.get("provider_voice_id"),
            model_id=voice.get("model_id"),
            speed=speed,
            provider=voice.get("provider"),
            use_cache=True,
        )
        
        await db.execute(
            "UPDATE voices SET preview_url = ?, updated_at = ? WHERE id = ?",
            (result.get("audio_url"), datetime.utcnow().isoformat(), voice_id)
        )
        
        return result
    
    def _get_preview_text(self, language: str) -> str:
        preview_texts = {
            "en": "Hello! I'm excited to chat with you. How are you doing today?",
            "zh": "你好！很高兴和你聊天。今天过得怎么样？",
            "ja": "こんにちは！お話しできることを楽しみにしています。今日はいかがですか？",
            "ko": "안녕하세요! 당신과 대화할 수 있어서 기컐요. 오늘 어떻게 지내세요?",
        }
        return preview_texts.get(language, preview_texts["en"])
    
    async def sync_from_elevenlabs(self) -> Dict[str, Any]:
        el_api_key = await get_config_value("ELEVENLABS_API_KEY", self.settings.elevenlabs_api_key)
        el_base_url = await get_config_value("ELEVENLABS_BASE_URL", self.settings.elevenlabs_base_url)
        if not el_api_key:
            return {"success": False, "error": "ElevenLabs API key not configured"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{el_base_url}/voices",
                    headers={"xi-api-key": el_api_key}
                )
                
                if response.status_code != 200:
                    return {"success": False, "error": f"ElevenLabs API error: {response.text}"}
                
                data = response.json()
                voices_data = data.get("voices", [])
                
                synced_count = 0
                skipped_count = 0
                
                for voice_data in voices_data:
                    provider_voice_id = voice_data.get("voice_id")
                    name = voice_data.get("name")
                    
                    existing = await db.execute(
                        "SELECT id FROM voices WHERE provider = ? AND provider_voice_id = ?",
                        ("elevenlabs", provider_voice_id),
                        fetch=True
                    )
                    
                    if existing:
                        skipped_count += 1
                        continue
                    
                    labels = voice_data.get("labels", {})
                    gender = labels.get("gender", "female").lower()
                    accent = labels.get("accent", "")
                    use_case = voice_data.get("use_case", "")
                    
                    tone = self._map_elevenlabs_labels_to_tone(labels)
                    language = self._map_accent_to_language(accent)
                    
                    preview_url = voice_data.get("preview_url")
                    
                    await self.create_voice({
                        "id": f"voice_el_{provider_voice_id[:12]}",
                        "name": name,
                        "display_name": f"{name} (ElevenLabs)",
                        "description": f"Accent: {accent}, Use case: {use_case}",
                        "preview_url": preview_url,
                        "provider": "elevenlabs",
                        "provider_voice_id": provider_voice_id,
                        "model_id": "eleven_multilingual_v2",
                        "language": language,
                        "gender": gender if gender in ["male", "female", "neutral"] else "female",
                        "tone": tone,
                        "settings": {"stability": 0.5, "similarity_boost": 0.75},
                        "is_active": True,
                    })
                    
                    synced_count += 1
                
                return {
                    "success": True,
                    "synced": synced_count,
                    "skipped": skipped_count,
                    "total": len(voices_data),
                }
            
        except Exception as e:
            logger.error(f"ElevenLabs sync failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def sync_from_dashscope(self) -> Dict[str, Any]:
        known_dashscope_voices = [
            {"provider_voice_id": "zhixiaoxia", "name": "知小夏", "gender": "female", "tone": "sweet"},
            {"provider_voice_id": "zhixiaoyao", "name": "知小瑶", "gender": "female", "tone": "lively"},
            {"provider_voice_id": "zhichu", "name": "知楚", "gender": "female", "tone": "mature"},
            {"provider_voice_id": "zhiyan", "name": "知燕", "gender": "female", "tone": "elegant"},
            {"provider_voice_id": "zhimiao", "name": "知妙", "gender": "female", "tone": "lively"},
            {"provider_voice_id": "zhiying", "name": "知英", "gender": "male", "tone": "calm"},
            {"provider_voice_id": "zhihao", "name": "知浩", "gender": "male", "tone": "confident"},
            {"provider_voice_id": "zhiya", "name": "知雅", "gender": "female", "tone": "elegant"},
            {"provider_voice_id": "aikan", "name": "艾侃", "gender": "male", "tone": "news"},
        ]
        
        synced_count = 0
        skipped_count = 0
        
        for voice_data in known_dashscope_voices:
            provider_voice_id = voice_data["provider_voice_id"]
            
            existing = await db.execute(
                "SELECT id FROM voices WHERE provider = ? AND provider_voice_id = ?",
                ("dashscope", provider_voice_id),
                fetch=True
            )
            
            if existing:
                skipped_count += 1
                continue
            
            await self.create_voice({
                "id": f"voice_ds_{provider_voice_id}",
                "name": voice_data["name"],
                "display_name": f"{voice_data['name']} (通义千问)",
                "description": f"阿里云语音合成音色 - {voice_data['tone']}",
                "provider": "dashscope",
                "provider_voice_id": provider_voice_id,
                "language": "zh",
                "gender": voice_data["gender"],
                "tone": voice_data["tone"],
                "settings": {"speed": 1.0, "pitch": 0},
                "is_active": True,
            })
            
            synced_count += 1
        
        return {
            "success": True,
            "synced": synced_count,
            "skipped": skipped_count,
            "total": len(known_dashscope_voices),
        }
    
    def _map_elevenlabs_labels_to_tone(self, labels: Dict[str, str]) -> str:
        use_case = labels.get("use_case", "").lower()
        description = labels.get("description", "").lower()
        
        tone_mapping = {
            "narrative": "calm",
            "conversational": "friendly",
            "characters": "expressive",
            "news": "professional",
            "audiobook": "warm",
            "announcement": "energetic",
            "podcast": "friendly",
            "meditation": "calm",
            "asmr": "asmr",
        }
        
        if use_case in tone_mapping:
            return tone_mapping[use_case]
        
        tone_keywords = {
            "seductive": ["sexy", "seductive", "sensual", "flirty"],
            "calm": ["calm", "peaceful", "relaxed", "meditation"],
            "warm": ["warm", "friendly", "kind", "soft"],
            "lively": ["energetic", "lively", "upbeat", "cheerful"],
            "mature": ["mature", "professional", "serious"],
            "asmr": ["asmr", "whisper", "soft"],
        }
        
        combined = f"{use_case} {description}".lower()
        for tone, keywords in tone_keywords.items():
            if any(kw in combined for kw in keywords):
                return tone
        
        return "warm"
    
    def _map_accent_to_language(self, accent: str) -> str:
        accent_language_map = {
            "american": "en",
            "british": "en",
            "australian": "en",
            "indian": "en",
            "irish": "en",
            "scottish": "en",
            "english": "en",
            "chinese": "zh",
            "mandarin": "zh",
            "japanese": "ja",
            "korean": "ko",
            "german": "de",
            "french": "fr",
            "spanish": "es",
            "italian": "it",
            "portuguese": "pt",
            "russian": "ru",
        }
        
        accent_lower = accent.lower()
        return accent_language_map.get(accent_lower, "en")


voice_management_service = VoiceManagementService()