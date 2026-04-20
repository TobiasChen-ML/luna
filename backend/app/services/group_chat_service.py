import json
import logging
import asyncio
from typing import Any, Optional, AsyncGenerator
from datetime import datetime

from app.core.database import db
from app.models.chat_session import (
    generate_session_id,
    generate_message_id,
)
from app.services.llm_service import LLMService
from app.services.character_service import character_service
from app.services.relationship_service import relationship_service
from app.services.redis_service import RedisService

logger = logging.getLogger(__name__)

GROUP_CHAT_HISTORY_TTL = 86400
MAX_CONCURRENT_LLM = 3

GROUP_CHAT_SYSTEM_TEMPLATE = """You are {{character_name}} participating in a group conversation.

{% if other_characters %}
Other participants in this conversation:
{% for char in other_characters %}
- {{char.name}}{% if char.personality_summary %}: {{char.personality_summary}}{% endif %}
{% endfor %}
{% endif %}

Guidelines:
1. Respond naturally as your character
2. React to what others say when appropriate
3. Stay in character at all times
4. Don't repeat what others have already said
5. Keep responses concise (2-4 sentences)

{% if personality_summary %}Your personality: {{personality_summary}}{% endif %}
{% if backstory %}Your background: {{backstory}}{% endif %}
"""

GROUP_CHAT_USER_TEMPLATE = """{{user_name}}: {{message}}"""


class GroupChatService:
    _instance = None
    
    def __init__(self):
        self.redis = RedisService()
        self.llm = None
    
    @classmethod
    def get_instance(cls) -> "GroupChatService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _get_llm(self) -> LLMService:
        if self.llm is None:
            self.llm = LLMService.get_instance()
        return self.llm
    
    async def create_group_session(
        self,
        user_id: str,
        participants: list[str],
        title: Optional[str] = None,
    ) -> dict:
        session_id = generate_session_id()
        now = datetime.utcnow().isoformat()
        
        await db.execute(
            """INSERT INTO chat_sessions
               (id, user_id, character_id, participants, quest_progress, context, created_at, updated_at)
               VALUES (?, ?, ?, ?, 0, ?, ?, ?)""",
            (
                session_id,
                user_id,
                participants[0] if participants else "",
                json.dumps(participants),
                json.dumps({"is_group": True}),
                now,
                now,
            )
        )
        
        logger.info(f"Created group chat session: {session_id} with participants: {participants}")
        return await self.get_session(session_id)
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        row = await db.execute(
            "SELECT * FROM chat_sessions WHERE id = ?",
            (session_id,),
            fetch=True
        )
        if row:
            result = dict(row)
            if result.get("participants") and isinstance(result["participants"], str):
                try:
                    result["participants"] = json.loads(result["participants"])
                except json.JSONDecodeError:
                    result["participants"] = []
            return result
        return None
    
    async def get_or_create_session(
        self,
        user_id: str,
        participants: list[str],
        session_id: Optional[str] = None,
    ) -> dict:
        if session_id:
            existing = await self.get_session(session_id)
            if existing:
                return existing
        
        return await self.create_group_session(user_id, participants)
    
    async def save_group_message(
        self,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        speaker_id: Optional[str] = None,
    ) -> dict:
        message_id = generate_message_id()
        
        await db.execute(
            """INSERT INTO chat_messages
               (id, session_id, role, content, character_id, user_id, speaker_id, message_type, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'text', ?)""",
            (
                message_id,
                session_id,
                role,
                content,
                speaker_id or "",
                user_id,
                speaker_id,
                datetime.utcnow().isoformat(),
            )
        )
        
        await db.execute(
            "UPDATE chat_sessions SET last_message_at = ?, updated_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), session_id)
        )
        
        return await self._get_message(message_id)
    
    async def _get_message(self, message_id: str) -> Optional[dict]:
        row = await db.execute(
            "SELECT * FROM chat_messages WHERE id = ?",
            (message_id,),
            fetch=True
        )
        return dict(row) if row else None
    
    async def get_group_messages(
        self,
        session_id: str,
        limit: int = 20,
    ) -> list[dict]:
        rows = await db.execute(
            "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC LIMIT ?",
            (session_id, limit),
            fetch_all=True
        )
        return [dict(row) for row in rows]
    
    async def _build_character_prompt(
        self,
        character_id: str,
        user_id: str,
        other_characters: list[dict],
    ) -> str:
        character = await character_service.get_character_by_id(character_id)
        if not character:
            character = {"name": "Assistant"}
        
        rel = await relationship_service.get_relationship(user_id, character_id)
        
        from jinja2 import Template
        
        other_chars_info = [
            {
                "name": c.get("name", "Unknown"),
                "personality_summary": c.get("personality_summary", "")
            }
            for c in other_characters if c.get("id") != character_id
        ]
        
        prompt = Template(GROUP_CHAT_SYSTEM_TEMPLATE).render(
            character_name=character.get("name", "Assistant"),
            other_characters=other_chars_info,
            personality_summary=character.get("personality_summary"),
            backstory=character.get("backstory"),
        )
        
        return prompt
    
    async def stream_character_response(
        self,
        character_id: str,
        user_id: str,
        message: str,
        conversation_history: list[dict],
        other_characters: list[dict],
    ) -> AsyncGenerator[dict, None]:
        llm = self._get_llm()
        
        system_prompt = await self._build_character_prompt(
            character_id, user_id, other_characters
        )
        
        messages = [{"role": "system", "content": system_prompt}]
        
        for msg in conversation_history[-10:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            speaker_id = msg.get("speaker_id")
            
            if role == "user":
                messages.append({"role": "user", "content": content})
            else:
                if speaker_id:
                    char = await character_service.get_character_by_id(speaker_id)
                    speaker_name = char.get("name", "Assistant") if char else "Assistant"
                    messages.append({"role": "assistant", "content": f"[{speaker_name}]: {content}"})
                else:
                    messages.append({"role": "assistant", "content": content})
        
        messages.append({"role": "user", "content": message})
        
        character = await character_service.get_character_by_id(character_id)
        character_name = character.get("name", "Assistant") if character else "Assistant"
        
        full_response = ""
        try:
            async for chunk in llm.generate_stream(messages=messages, temperature=0.8, max_tokens=300):
                if chunk:
                    full_response += chunk
                    yield {
                        "event": "text_delta",
                        "data": {
                            "speaker_id": character_id,
                            "speaker_name": character_name,
                            "content": chunk
                        }
                    }
            
            yield {
                "event": "text_done",
                "data": {
                    "speaker_id": character_id,
                    "speaker_name": character_name,
                    "full_content": full_response
                }
            }
            
        except Exception as e:
            logger.error(f"LLM stream failed for character {character_id}: {e}")
            yield {
                "event": "error",
                "data": {
                    "speaker_id": character_id,
                    "error": str(e)
                }
            }
    
    async def stream_parallel_responses(
        self,
        participants: list[str],
        user_id: str,
        message: str,
        conversation_history: list[dict],
    ) -> AsyncGenerator[dict, None]:
        characters = []
        for char_id in participants:
            char = await character_service.get_character_by_id(char_id)
            if char:
                characters.append(char)
        
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_LLM)
        
        async def controlled_stream(char_id: str):
            async with semaphore:
                async for event in self.stream_character_response(
                    char_id, user_id, message, conversation_history, characters
                ):
                    yield event
        
        streams = [controlled_stream(char_id) for char_id in participants]
        
        pending = {}
        for i, stream in enumerate(streams):
            try:
                agen = stream.__aiter__()
                pending[agen] = participants[i]
            except Exception as e:
                logger.error(f"Failed to create stream for {participants[i]}: {e}")
        
        while pending:
            done, _ = await asyncio.wait(
                pending.keys(),
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for agen in done:
                char_id = pending[agen]
                try:
                    while True:
                        event = await agen.__anext__()
                        yield event
                except StopAsyncIteration:
                    pass
                except Exception as e:
                    logger.error(f"Error in stream for {char_id}: {e}")
                    yield {
                        "event": "error",
                        "data": {"speaker_id": char_id, "error": str(e)}
                    }
                finally:
                    del pending[agen]


group_chat_service = GroupChatService()
