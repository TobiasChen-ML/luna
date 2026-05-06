import base64
import json
from unittest.mock import AsyncMock

import pytest

from app.services.realtime_session_manager import (
    RealtimeCharacterContext,
    RealtimeSessionManager,
    RealtimeSession,
    RealtimeSessionState,
)


def test_build_initiation_payload_injects_prompt_memory_and_voice():
    manager = RealtimeSessionManager(
        memory_service=AsyncMock(),
        character_service=AsyncMock(),
        http_client=AsyncMock(),
    )
    context = RealtimeCharacterContext(
        character_id="char_001",
        user_id="user_001",
        voice_id="voice_abc",
        system_prompt="You are Roxy.",
        memory_text="Relationship summary: user likes quiet mornings.",
        first_message="Good morning. I remember what you told me.",
        character_name="Roxy",
    )

    payload = manager.build_initiation_payload(context)

    assert payload["type"] == "conversation_initiation_client_data"
    override = payload["conversation_config_override"]
    assert "You are Roxy." in override["agent"]["prompt"]["prompt"]
    assert "quiet mornings" in override["agent"]["prompt"]["prompt"]
    assert override["agent"]["first_message"] == "Good morning. I remember what you told me."
    assert override["tts"]["voice_id"] == "voice_abc"
    assert payload["dynamic_variables"]["user_id"] == "user_001"
    assert "user_id" not in payload


def test_normalize_binary_audio_json_alias():
    manager = RealtimeSessionManager(
        memory_service=AsyncMock(),
        character_service=AsyncMock(),
        http_client=AsyncMock(),
    )
    raw_audio = b"pcm-bytes"
    payload = manager._normalize_client_text_message(
        json.dumps({"audio_base64": base64.b64encode(raw_audio).decode("ascii")})
    )

    assert payload == {"user_audio_chunk": base64.b64encode(raw_audio).decode("ascii")}


@pytest.mark.asyncio
async def test_load_character_context_uses_memory_service():
    memory = AsyncMock()
    memory.get_context = AsyncMock(
        return_value={
            "working_memory": [{"content": "The user asked about Tokyo."}],
            "episodic_summary": "They planned a trip together.",
            "semantic_facts": ["The user prefers soft voices."],
            "global_memories": [{"content": "The user likes late-night calls."}],
        }
    )
    character_service = AsyncMock()
    character_service.get_character_by_id = AsyncMock(
        return_value={
            "id": "char_001",
            "name": "Roxy",
            "voice_id": "voice_abc",
            "system_prompt": "Stay warm and concise.",
            "greeting": "Hey, I was thinking about you.",
        }
    )
    manager = RealtimeSessionManager(
        memory_service=memory,
        character_service=character_service,
        http_client=AsyncMock(),
    )
    manager._get_character_voice_map = AsyncMock(return_value={})
    manager._resolve_voice_db_id = AsyncMock(return_value=None)

    context = await manager.load_character_context("char_001", "user_001")

    assert context.voice_id == "voice_abc"
    assert context.system_prompt == "Stay warm and concise."
    assert "Tokyo" in context.memory_text
    assert "soft voices" in context.memory_text
    assert context.first_message == "Hey, I was thinking about you."


@pytest.mark.asyncio
async def test_persist_conversation_memory_extracts_transcript_and_summary():
    memory = AsyncMock()
    manager = RealtimeSessionManager(
        memory_service=memory,
        character_service=AsyncMock(),
        http_client=AsyncMock(),
    )
    manager._fetch_conversation = AsyncMock(
        return_value={
            "transcript": [
                {"role": "user", "message": "I got the job."},
                {"role": "agent", "message": "I am proud of you."},
            ],
            "analysis": {"transcript_summary": "The user shared that they got the job."},
        }
    )
    session = RealtimeSession(
        session_id="rt_001",
        user_id="user_001",
        character_id="char_001",
        conversation_id="conv_001",
    )

    await manager._persist_conversation_memory(session)

    memory.extract_and_store.assert_awaited_once()
    memory.add_memory.assert_awaited_once()
    assert memory.add_memory.await_args.kwargs["metadata"]["conversation_id"] == "conv_001"


@pytest.mark.asyncio
async def test_agent_response_complete_does_not_close_session():
    manager = RealtimeSessionManager(
        memory_service=AsyncMock(),
        character_service=AsyncMock(),
        http_client=AsyncMock(),
    )
    eleven_ws = AsyncMock()
    client_ws = AsyncMock()
    session = RealtimeSession(
        session_id="rt_001",
        user_id="user_001",
        character_id="char_001",
        state=RealtimeSessionState.ACTIVE,
    )

    should_stop = await manager._handle_eleven_event(
        {"type": "agent_response_complete"},
        eleven_ws,
        client_ws,
        session,
    )

    assert should_stop is False
    assert session.state == RealtimeSessionState.ACTIVE
    client_ws.send_json.assert_awaited_once()


@pytest.mark.asyncio
async def test_conversation_end_closes_session():
    manager = RealtimeSessionManager(
        memory_service=AsyncMock(),
        character_service=AsyncMock(),
        http_client=AsyncMock(),
    )
    eleven_ws = AsyncMock()
    client_ws = AsyncMock()
    session = RealtimeSession(
        session_id="rt_001",
        user_id="user_001",
        character_id="char_001",
        state=RealtimeSessionState.ACTIVE,
    )

    should_stop = await manager._handle_eleven_event(
        {"type": "conversation_ended"},
        eleven_ws,
        client_ws,
        session,
    )

    assert should_stop is True
    assert session.state == RealtimeSessionState.CLOSING
    client_ws.send_json.assert_awaited_once()
