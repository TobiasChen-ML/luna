import json
import logging
from typing import Optional, Any
from datetime import datetime
from threading import Lock

from app.core.database import db
from app.services.redis_service import RedisService
from app.models.chat_session import (
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatMessageCreate,
    generate_session_id,
    generate_message_id,
)

logger = logging.getLogger(__name__)

HISTORY_LIMIT = 20
REDIS_HISTORY_TTL = 86400
REDIS_FAILURE_THRESHOLD = 3


class ChatHistoryService:
    _instance = None
    
    def __init__(self):
        self.redis = RedisService()
        self._redis_failure_count = 0
        self._redis_degraded = False
        self._failure_lock = Lock()
    
    @classmethod
    def get_instance(cls) -> "ChatHistoryService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _record_redis_failure(self, session_id: str, operation: str, error: Exception) -> None:
        with self._failure_lock:
            self._redis_failure_count += 1
            if self._redis_failure_count >= REDIS_FAILURE_THRESHOLD and not self._redis_degraded:
                self._redis_degraded = True
                logger.error(
                    f"Redis cache degraded after {self._redis_failure_count} failures. "
                    f"session={session_id}, operation={operation}, error={error}"
                )
            else:
                logger.warning(
                    f"Redis operation failed ({self._redis_failure_count}/{REDIS_FAILURE_THRESHOLD}): "
                    f"session={session_id}, operation={operation}, error={error}"
                )
    
    def _record_redis_success(self) -> None:
        with self._failure_lock:
            if self._redis_failure_count > 0:
                self._redis_failure_count = 0
            if self._redis_degraded:
                self._redis_degraded = False
                logger.info("Redis cache recovered, degradation cleared")
    
    async def redis_health_check(self) -> dict[str, Any]:
        try:
            await self.redis.get("__health_check__")
            self._record_redis_success()
            return {"healthy": True, "degraded": False}
        except Exception as e:
            return {"healthy": False, "degraded": self._redis_degraded, "error": str(e)}
    
    async def get_or_create_session(
        self,
        user_id: str,
        character_id: str,
        session_id: Optional[str] = None,
        script_id: Optional[str] = None,
    ) -> dict:
        if session_id:
            existing = await self.get_session(session_id)
            if existing:
                return existing
        
        return await self.create_session(ChatSessionCreate(
            user_id=user_id,
            character_id=character_id,
            script_id=script_id,
        ))
    
    async def create_session(self, data: ChatSessionCreate) -> dict:
        session_id = generate_session_id()
        now = datetime.utcnow().isoformat()
        
        await db.execute(
            """INSERT INTO chat_sessions
               (id, user_id, character_id, script_id, quest_progress, context, created_at, updated_at)
               VALUES (?, ?, ?, ?, 0, ?, ?, ?)""",
            (
                session_id,
                data.user_id,
                data.character_id,
                data.script_id,
                json.dumps(data.context) if data.context else None,
                now,
                now,
            )
        )
        
        logger.info(f"Created chat session: {session_id}")
        return await self.get_session(session_id)
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        row = await db.execute(
            "SELECT * FROM chat_sessions WHERE id = ?",
            (session_id,),
            fetch=True
        )
        return self._session_row_to_dict(row) if row else None
    
    async def get_user_sessions(
        self,
        user_id: str,
        character_id: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        conditions = ["user_id = ?"]
        params = [user_id]
        
        if character_id:
            conditions.append("character_id = ?")
            params.append(character_id)
        
        query = f"SELECT * FROM chat_sessions WHERE {' AND '.join(conditions)} ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        
        rows = await db.execute(query, tuple(params), fetch_all=True)
        return [self._session_row_to_dict(row) for row in rows]
    
    async def update_session(self, session_id: str, data: ChatSessionUpdate) -> Optional[dict]:
        existing = await self.get_session(session_id)
        if not existing:
            return None
        
        updates = []
        params = []
        
        for field in ["title", "script_id", "script_state", "script_node_id", "quest_progress"]:
            value = getattr(data, field, None)
            if value is not None:
                updates.append(f"{field} = ?")
                params.append(value)
        
        if data.context is not None:
            updates.append("context = ?")
            params.append(json.dumps(data.context))
        
        if not updates:
            return existing
        
        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(session_id)
        
        await db.execute(
            f"UPDATE chat_sessions SET {', '.join(updates)} WHERE id = ?",
            tuple(params)
        )
        
        return await self.get_session(session_id)
    
    async def update_session_last_message(self, session_id: str) -> None:
        await db.execute(
            "UPDATE chat_sessions SET last_message_at = ?, updated_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), session_id)
        )
    
    async def save_message(self, data: ChatMessageCreate) -> dict:
        message_id = generate_message_id()
        
        await db.execute(
            """INSERT INTO chat_messages
               (id, session_id, role, content, character_id, user_id, message_type,
                audio_url, image_urls, metadata, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                message_id,
                data.session_id,
                data.role,
                data.content,
                data.character_id,
                data.user_id,
                data.message_type.value if hasattr(data.message_type, 'value') else data.message_type,
                data.audio_url,
                json.dumps(data.image_urls) if data.image_urls else None,
                json.dumps(data.metadata) if data.metadata else None,
                datetime.utcnow().isoformat(),
            )
        )
        
        await self._cache_message(data.session_id, message_id, data.role, data.content)
        await self.update_session_last_message(data.session_id)
        
        return await self.get_message(message_id)
    
    async def get_message(self, message_id: str) -> Optional[dict]:
        row = await db.execute(
            "SELECT * FROM chat_messages WHERE id = ?",
            (message_id,),
            fetch=True
        )
        return self._message_row_to_dict(row) if row else None
    
    async def get_recent_messages(
        self,
        session_id: str,
        limit: int = HISTORY_LIMIT,
    ) -> list[dict]:
        cached = await self._get_cached_messages(session_id)
        
        if cached and len(cached) >= limit:
            return cached[-limit:]
        
        rows = await db.execute(
            "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC LIMIT ?",
            (session_id, limit),
            fetch_all=True
        )
        
        messages = [self._message_row_to_dict(row) for row in rows]
        
        if messages:
            await self._cache_messages_bulk(session_id, messages)
        
        return messages
    
    async def get_messages_before(
        self,
        session_id: str,
        before_message_id: str,
        limit: int = 20,
    ) -> list[dict]:
        before_msg = await self.get_message(before_message_id)
        if not before_msg:
            return []
        
        rows = await db.execute(
            """SELECT * FROM chat_messages 
               WHERE session_id = ? AND created_at < ? 
               ORDER BY created_at DESC LIMIT ?""",
            (session_id, before_msg["created_at"], limit),
            fetch_all=True
        )
        
        return [self._message_row_to_dict(row) for row in rows]
    
    async def _cache_message(
        self,
        session_id: str,
        message_id: str,
        role: str,
        content: str,
    ) -> None:
        key = f"chat_history:{session_id}"
        
        try:
            cached = await self.redis.get_json(key)
            if not isinstance(cached, dict):
                cached = {}
            messages = cached.get("messages", [])
            if not isinstance(messages, list):
                messages = []
            safe_content = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
            
            messages.append({
                "id": message_id,
                "role": role,
                "content": safe_content,
                "created_at": datetime.utcnow().isoformat(),
            })
            
            messages = messages[-50:]
            
            await self.redis.set_json(key, {"messages": messages}, ex=REDIS_HISTORY_TTL)
            self._record_redis_success()
        except Exception as e:
            self._record_redis_failure(session_id, "cache_message", e)
    
    async def _cache_messages_bulk(
        self,
        session_id: str,
        messages: list[dict],
    ) -> None:
        key = f"chat_history:{session_id}"
        
        try:
            data = {
                "messages": [
                    {"id": m["id"], "role": m["role"], "content": m["content"], "created_at": m["created_at"]}
                    for m in messages[-50:]
                ]
            }
            await self.redis.set_json(key, data, ex=REDIS_HISTORY_TTL)
            self._record_redis_success()
        except Exception as e:
            self._record_redis_failure(session_id, "cache_messages_bulk", e)
    
    async def _get_cached_messages(self, session_id: str) -> Optional[list[dict]]:
        key = f"chat_history:{session_id}"
        
        try:
            cached = await self.redis.get_json(key)
            if cached:
                self._record_redis_success()
                return cached.get("messages", [])
        except Exception as e:
            self._record_redis_failure(session_id, "get_cached_messages", e)
        
        return None
    
    def _session_row_to_dict(self, row: dict) -> dict:
        result = dict(row)
        if result.get("context") and isinstance(result["context"], str):
            try:
                result["context"] = json.loads(result["context"])
            except json.JSONDecodeError:
                result["context"] = {}
        return result
    
    def _message_row_to_dict(self, row: dict) -> dict:
        result = dict(row)
        for field in ["image_urls", "metadata"]:
            if result.get(field) and isinstance(result[field], str):
                try:
                    result[field] = json.loads(result[field])
                except json.JSONDecodeError:
                    result[field] = [] if field == "image_urls" else {}
        if "image_urls" not in result:
            result["image_urls"] = []
        if "metadata" not in result:
            result["metadata"] = {}
        return result


chat_history_service = ChatHistoryService()
