import asyncio
import base64
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from urllib.parse import urlencode

import httpx
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from app.core.config import get_config_value
from app.core.database import db
from app.services.character_service import CharacterService
from app.services.memory_service import MemoryService

logger = logging.getLogger(__name__)


class RealtimeSessionState(str, Enum):
    INITIALIZING = "initializing"
    CONNECTING = "connecting"
    ACTIVE = "active"
    CLOSING = "closing"
    CLOSED = "closed"
    FAILED = "failed"


@dataclass
class RealtimeCharacterContext:
    character_id: str
    user_id: str
    voice_id: str
    system_prompt: str
    memory_text: str
    first_message: str
    character_name: str = "AI"


@dataclass
class RealtimeSession:
    session_id: str
    user_id: str
    character_id: str
    state: RealtimeSessionState = RealtimeSessionState.INITIALIZING
    conversation_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None
    error: Optional[str] = None


class RealtimeSessionManager:
    def __init__(
        self,
        memory_service: Optional[MemoryService] = None,
        character_service: Optional[CharacterService] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        self.memory_service = memory_service or MemoryService()
        self.character_service = character_service or CharacterService.get_instance()
        self.http_client = http_client or httpx.AsyncClient(timeout=30.0)
        self._sessions: dict[str, RealtimeSession] = {}
        self._lock = asyncio.Lock()

    async def handle_client(
        self,
        websocket: WebSocket,
        *,
        user_id: str,
        character_id: str,
        session_id: Optional[str] = None,
    ) -> None:
        session = RealtimeSession(
            session_id=session_id or f"rt_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            character_id=character_id,
        )
        await self._register_session(session)

        try:
            await websocket.accept()
            context = await self.load_character_context(character_id, user_id)
            session.state = RealtimeSessionState.CONNECTING

            eleven_ws = await self._connect_elevenlabs()
            try:
                await self._send_initiation(eleven_ws, context)
                session.state = RealtimeSessionState.ACTIVE
                await websocket.send_json(
                    {
                        "type": "realtime_session_started",
                        "session_id": session.session_id,
                        "character_id": character_id,
                        "voice_id": context.voice_id,
                    }
                )
                await self._relay_until_closed(websocket, eleven_ws, session)
            finally:
                await self._close_elevenlabs(eleven_ws)
        except WebSocketDisconnect:
            logger.info("Realtime client disconnected: session=%s", session.session_id)
        except Exception as exc:
            session.state = RealtimeSessionState.FAILED
            session.error = str(exc)
            logger.exception("Realtime session failed: session=%s", session.session_id)
            await self._close_client_with_error(websocket, exc)
        finally:
            session.state = RealtimeSessionState.CLOSING
            await self._finalize_session(session)
            await self._unregister_session(session.session_id)

    async def load_character_context(self, character_id: str, user_id: str) -> RealtimeCharacterContext:
        character = await self.character_service.get_character_by_id(character_id)
        if not character:
            raise ValueError("Character not found")

        voice_id = await self._resolve_character_voice_id(character)
        if not voice_id:
            raise ValueError("Character voice is not configured")

        system_prompt = self._build_character_prompt(character)
        memory_text = await self._load_memory_text(user_id, character_id)
        first_message = self._build_first_message(character, memory_text)

        return RealtimeCharacterContext(
            character_id=character_id,
            user_id=user_id,
            voice_id=voice_id,
            system_prompt=system_prompt,
            memory_text=memory_text,
            first_message=first_message,
            character_name=character.get("name") or character.get("first_name") or "AI",
        )

    def build_initiation_payload(self, context: RealtimeCharacterContext) -> dict[str, Any]:
        prompt_parts = [context.system_prompt.strip()]
        if context.memory_text.strip():
            prompt_parts.append(
                "Relevant memory for this user and character:\n"
                f"{context.memory_text.strip()}"
            )

        return {
            "type": "conversation_initiation_client_data",
            "conversation_config_override": {
                "agent": {
                    "prompt": {
                        "prompt": "\n\n".join(part for part in prompt_parts if part),
                    },
                    "first_message": context.first_message,
                },
                "tts": {
                    "voice_id": context.voice_id,
                },
            },
            "dynamic_variables": {
                "character_id": context.character_id,
                "character_name": context.character_name,
                "user_id": context.user_id,
            },
        }

    async def _connect_elevenlabs(self):
        import websockets

        url = await self._get_elevenlabs_ws_url()
        retries = int(await get_config_value("ELEVENLABS_REALTIME_CONNECT_RETRIES", "1") or "1")
        last_exc: Optional[Exception] = None

        for attempt in range(retries + 1):
            try:
                return await websockets.connect(
                    url,
                    max_size=8 * 1024 * 1024,
                    open_timeout=10,
                    ping_interval=None,
                )
            except Exception as exc:
                last_exc = exc
                if attempt >= retries:
                    break
                await asyncio.sleep(0.25 * (attempt + 1))

        raise ConnectionError(f"Could not connect to ElevenLabs realtime API: {last_exc}")

    async def _close_elevenlabs(self, eleven_ws: Any) -> None:
        try:
            await eleven_ws.close()
        except Exception:
            pass

    async def _get_elevenlabs_ws_url(self) -> str:
        agent_id = await get_config_value("ELEVENLABS_CONVAI_BASE_AGENT_ID")
        if not agent_id:
            raise ValueError("ELEVENLABS_CONVAI_BASE_AGENT_ID is not configured")

        use_signed_url = (
            await get_config_value("ELEVENLABS_CONVAI_USE_SIGNED_URL", "false") or "false"
        ).lower() == "true"
        if use_signed_url:
            signed_url = await self._get_signed_url(agent_id)
            if signed_url:
                return signed_url

        query = urlencode({"agent_id": agent_id})
        return f"wss://api.elevenlabs.io/v1/convai/conversation?{query}"

    async def _get_signed_url(self, agent_id: str) -> Optional[str]:
        api_key = await get_config_value("ELEVENLABS_API_KEY")
        base_url = await get_config_value("ELEVENLABS_BASE_URL", "https://api.elevenlabs.io/v1")
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY is required when signed URLs are enabled")

        response = await self.http_client.get(
            f"{base_url}/convai/conversation/get-signed-url",
            params={"agent_id": agent_id},
            headers={"xi-api-key": api_key},
        )
        if response.status_code in (401, 402, 403, 429):
            raise RuntimeError(f"ElevenLabs authorization/quota error: {response.text}")
        response.raise_for_status()
        return response.json().get("signed_url")

    async def _send_initiation(self, eleven_ws: Any, context: RealtimeCharacterContext) -> None:
        await eleven_ws.send(json.dumps(self.build_initiation_payload(context)))

    async def _relay_until_closed(
        self,
        client_ws: WebSocket,
        eleven_ws: Any,
        session: RealtimeSession,
    ) -> None:
        client_to_eleven = asyncio.create_task(
            self._relay_client_to_eleven(client_ws, eleven_ws, session)
        )
        eleven_to_client = asyncio.create_task(
            self._relay_eleven_to_client(eleven_ws, client_ws, session)
        )
        done, pending = await asyncio.wait(
            {client_to_eleven, eleven_to_client},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        for task in done:
            exc = task.exception()
            if exc:
                raise exc

    async def _relay_client_to_eleven(
        self,
        client_ws: WebSocket,
        eleven_ws: Any,
        session: RealtimeSession,
    ) -> None:
        while session.state == RealtimeSessionState.ACTIVE:
            message = await client_ws.receive()
            if message.get("type") == "websocket.disconnect":
                session.state = RealtimeSessionState.CLOSING
                await eleven_ws.close()
                return

            if message.get("bytes") is not None:
                await eleven_ws.send(
                    json.dumps(
                        {
                            "user_audio_chunk": base64.b64encode(message["bytes"]).decode("ascii"),
                        }
                    )
                )
                continue

            text = message.get("text")
            if text is None:
                continue

            payload = self._normalize_client_text_message(text)
            if payload.get("type") in {"stop", "conversation_end"}:
                session.state = RealtimeSessionState.CLOSING
                await eleven_ws.close()
                return
            await eleven_ws.send(json.dumps(payload))

    async def _relay_eleven_to_client(
        self,
        eleven_ws: Any,
        client_ws: WebSocket,
        session: RealtimeSession,
    ) -> None:
        async for raw_message in eleven_ws:
            if isinstance(raw_message, bytes):
                await client_ws.send_bytes(raw_message)
                continue

            payload = json.loads(raw_message)
            should_stop = await self._handle_eleven_event(payload, eleven_ws, client_ws, session)
            if should_stop:
                return

    async def _handle_eleven_event(
        self,
        payload: dict[str, Any],
        eleven_ws: Any,
        client_ws: WebSocket,
        session: RealtimeSession,
    ) -> bool:
        event_type = payload.get("type")
        if event_type == "conversation_initiation_metadata":
            metadata = payload.get("conversation_initiation_metadata_event") or {}
            session.conversation_id = metadata.get("conversation_id") or session.conversation_id
            await client_ws.send_json(payload)
            return False

        if event_type == "ping":
            ping_event = payload.get("ping_event") or {}
            event_id = ping_event.get("event_id")
            if event_id is not None:
                await eleven_ws.send(json.dumps({"type": "pong", "event_id": event_id}))
            return False

        if event_type == "audio":
            audio_event = payload.get("audio_event") or {}
            audio_b64 = audio_event.get("audio_base_64")
            if audio_b64:
                await client_ws.send_bytes(base64.b64decode(audio_b64))
            return False

        if event_type in {"conversation_ended", "conversation_end"}:
            await client_ws.send_json(payload)
            session.state = RealtimeSessionState.CLOSING
            return True

        await client_ws.send_json(payload)
        return False

    def _normalize_client_text_message(self, text: str) -> dict[str, Any]:
        try:
            payload = json.loads(text)
            if not isinstance(payload, dict):
                return {"type": "user_message", "text": text}
        except json.JSONDecodeError:
            return {"type": "user_message", "text": text}

        if "audio_base64" in payload and "user_audio_chunk" not in payload:
            return {"user_audio_chunk": payload["audio_base64"]}
        if "user_audio_chunk" in payload:
            return {"user_audio_chunk": payload["user_audio_chunk"]}
        return payload

    async def _resolve_character_voice_id(self, character: dict[str, Any]) -> Optional[str]:
        character_id = str(character.get("id") or "")
        configured_map = await self._get_character_voice_map()
        mapped_voice_id = configured_map.get(character_id)
        if mapped_voice_id:
            return mapped_voice_id

        voice_id = (character.get("voice_id") or "").strip()
        if not voice_id:
            return None

        provider_voice_id = await self._resolve_voice_db_id(voice_id)
        return provider_voice_id or voice_id

    async def _get_character_voice_map(self) -> dict[str, str]:
        raw_map = await get_config_value("REALTIME_CHARACTER_VOICE_MAP", "{}")
        try:
            parsed = json.loads(raw_map or "{}")
        except json.JSONDecodeError:
            logger.warning("REALTIME_CHARACTER_VOICE_MAP is not valid JSON")
            return {}
        if not isinstance(parsed, dict):
            return {}
        return {str(key): str(value) for key, value in parsed.items() if value}

    async def _resolve_voice_db_id(self, voice_id: str) -> Optional[str]:
        try:
            row = await db.execute(
                "SELECT provider_voice_id FROM voices WHERE id = ? AND provider = 'elevenlabs' AND is_active = 1",
                (voice_id,),
                fetch=True,
            )
            if row:
                return row["provider_voice_id"]
        except Exception as exc:
            logger.warning("Failed to resolve voice mapping for %s: %s", voice_id, exc)
        return None

    def _build_character_prompt(self, character: dict[str, Any]) -> str:
        prompt = (character.get("system_prompt") or "").strip()
        if prompt:
            return prompt

        parts = [
            f"You are {character.get('name') or 'the character'}.",
            character.get("personality_summary") or "",
            character.get("backstory") or "",
            character.get("description") or "",
        ]
        return "\n".join(part.strip() for part in parts if part and part.strip())

    async def _load_memory_text(self, user_id: str, character_id: str) -> str:
        try:
            memory_context = await asyncio.wait_for(
                self.memory_service.get_context(character_id=character_id, user_id=user_id),
                timeout=float(await get_config_value("REALTIME_MEMORY_READ_TIMEOUT_SECONDS", "3.0") or "3.0"),
            )
        except asyncio.TimeoutError:
            logger.warning("Memory read timed out: user=%s character=%s", user_id, character_id)
            return ""
        except Exception as exc:
            logger.warning("Memory read failed: user=%s character=%s error=%s", user_id, character_id, exc)
            return ""

        return self._format_memory_context(memory_context)

    def _format_memory_context(self, memory_context: dict[str, Any]) -> str:
        lines: list[str] = []
        working = memory_context.get("working_memory") or []
        if working:
            lines.append("Recent context:")
            lines.extend(f"- {item.get('content')}" for item in working[:8] if item.get("content"))

        episodic_summary = memory_context.get("episodic_summary")
        if episodic_summary:
            lines.append(f"Relationship summary: {episodic_summary}")

        semantic_facts = memory_context.get("semantic_facts") or []
        if semantic_facts:
            lines.append("Known user facts:")
            lines.extend(f"- {fact}" for fact in semantic_facts[:12] if fact)

        global_memories = memory_context.get("global_memories") or []
        if global_memories:
            lines.append("Cross-character user context:")
            lines.extend(
                f"- {item.get('content')}"
                for item in global_memories[:8]
                if item.get("content")
            )

        return "\n".join(lines)

    def _build_first_message(self, character: dict[str, Any], memory_text: str) -> str:
        greeting = (character.get("greeting") or "").strip()
        name = character.get("first_name") or character.get("name") or "there"
        if memory_text:
            return greeting or f"Hi, it's {name}. I remember where we left off. How are you feeling now?"
        return greeting or f"Hi, it's {name}. I'm here with you."

    async def _finalize_session(self, session: RealtimeSession) -> None:
        session.closed_at = datetime.utcnow()
        if session.conversation_id:
            await self._persist_conversation_memory(session)
        session.state = RealtimeSessionState.CLOSED

    async def _persist_conversation_memory(self, session: RealtimeSession) -> None:
        try:
            conversation = await self._fetch_conversation(session.conversation_id)
            transcript = self._extract_transcript(conversation)
            if transcript:
                await self.memory_service.extract_and_store(
                    user_id=session.user_id,
                    character_id=session.character_id,
                    conversation=transcript,
                )

            summary = self._extract_summary(conversation)
            if summary:
                await self.memory_service.add_memory(
                    user_id=session.user_id,
                    character_id=session.character_id,
                    content=f"Voice call summary: {summary}",
                    layer="episodic",
                    importance=7,
                    metadata={
                        "source": "elevenlabs_realtime_call",
                        "conversation_id": session.conversation_id,
                        "session_id": session.session_id,
                    },
                )
        except Exception as exc:
            logger.warning(
                "Failed to persist realtime memory: session=%s conversation=%s error=%s",
                session.session_id,
                session.conversation_id,
                exc,
            )

    async def _fetch_conversation(self, conversation_id: str) -> dict[str, Any]:
        api_key = await get_config_value("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY is required to fetch conversation details")

        base_url = await get_config_value("ELEVENLABS_BASE_URL", "https://api.elevenlabs.io/v1")
        response = await self.http_client.get(
            f"{base_url}/convai/conversations/{conversation_id}",
            headers={"xi-api-key": api_key},
        )
        if response.status_code in (401, 402, 403, 429):
            raise RuntimeError(f"ElevenLabs conversation fetch failed: {response.text}")
        response.raise_for_status()
        return response.json()

    def _extract_transcript(self, conversation: dict[str, Any]) -> list[dict[str, str]]:
        transcript = conversation.get("transcript") or []
        normalized: list[dict[str, str]] = []
        for item in transcript:
            message = item.get("message") or item.get("text")
            role = item.get("role") or "assistant"
            if message:
                normalized.append({"role": role, "content": message})
        return normalized

    def _extract_summary(self, conversation: dict[str, Any]) -> Optional[str]:
        analysis = conversation.get("analysis") or {}
        for key in ("transcript_summary", "call_summary", "summary"):
            value = analysis.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    async def _register_session(self, session: RealtimeSession) -> None:
        async with self._lock:
            self._sessions[session.session_id] = session

    async def _unregister_session(self, session_id: str) -> None:
        async with self._lock:
            self._sessions.pop(session_id, None)

    async def get_session(self, session_id: str) -> Optional[RealtimeSession]:
        async with self._lock:
            return self._sessions.get(session_id)

    async def list_active_sessions(self) -> list[RealtimeSession]:
        async with self._lock:
            return list(self._sessions.values())

    async def _close_client_with_error(self, websocket: WebSocket, exc: Exception) -> None:
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
            await websocket.close(code=1011)
        except Exception:
            pass


realtime_session_manager = RealtimeSessionManager()
