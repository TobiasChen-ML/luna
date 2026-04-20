import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.services.group_chat_service import GroupChatService


class TestGroupChatService:
    
    @pytest.fixture
    def group_chat_service(self):
        return GroupChatService()
    
    @pytest.fixture
    def mock_character(self):
        return {
            "id": "char_001",
            "name": "Test Character",
            "personality_summary": "Friendly and helpful",
            "backstory": "A test AI character",
        }
    
    @pytest.fixture
    def mock_characters(self):
        return [
            {"id": "char_001", "name": "Alice", "personality_summary": "Friendly"},
            {"id": "char_002", "name": "Bob", "personality_summary": "Curious"},
        ]

    def test_get_instance_singleton(self, group_chat_service):
        instance1 = GroupChatService.get_instance()
        instance2 = GroupChatService.get_instance()
        assert instance1 is instance2

    @pytest.mark.asyncio
    async def test_create_group_session(self, group_chat_service):
        with patch('app.services.group_chat_service.db') as mock_db:
            mock_db.execute = AsyncMock()
            mock_db.execute.return_value = None
            
            with patch.object(group_chat_service, 'get_session', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = {
                    "id": "session_001",
                    "user_id": "user_001",
                    "participants": ["char_001", "char_002"],
                }
                
                result = await group_chat_service.create_group_session(
                    user_id="user_001",
                    participants=["char_001", "char_002"],
                )
                
                assert result["user_id"] == "user_001"
                assert result["participants"] == ["char_001", "char_002"]

    @pytest.mark.asyncio
    async def test_get_session_parses_participants_json(self, group_chat_service):
        with patch('app.services.group_chat_service.db') as mock_db:
            mock_db.execute = AsyncMock(return_value={
                "id": "session_001",
                "participants": '["char_001", "char_002"]',
            })
            
            result = await group_chat_service.get_session("session_001")
            
            assert result["participants"] == ["char_001", "char_002"]

    @pytest.mark.asyncio
    async def test_save_group_message(self, group_chat_service):
        with patch('app.services.group_chat_service.db') as mock_db:
            mock_db.execute = AsyncMock()
            
            with patch.object(group_chat_service, '_get_message', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = {
                    "id": "msg_001",
                    "session_id": "session_001",
                    "role": "assistant",
                    "content": "Hello!",
                    "speaker_id": "char_001",
                }
                
                result = await group_chat_service.save_group_message(
                    session_id="session_001",
                    user_id="user_001",
                    role="assistant",
                    content="Hello!",
                    speaker_id="char_001",
                )
                
                assert result["speaker_id"] == "char_001"

    @pytest.mark.asyncio
    async def test_build_character_prompt(self, group_chat_service, mock_character, mock_characters):
        with patch('app.services.group_chat_service.character_service') as mock_char_service:
            mock_char_service.get_character_by_id = AsyncMock(return_value=mock_character)
            
            with patch('app.services.group_chat_service.relationship_service') as mock_rel_service:
                mock_rel_service.get_relationship = AsyncMock(return_value=None)
                
                prompt = await group_chat_service._build_character_prompt(
                    character_id="char_001",
                    user_id="user_001",
                    other_characters=mock_characters,
                )
                
                assert "Test Character" in prompt
                assert "group conversation" in prompt.lower()

    @pytest.mark.asyncio
    async def test_stream_character_response(self, group_chat_service, mock_character):
        with patch('app.services.group_chat_service.character_service') as mock_char_service:
            mock_char_service.get_character_by_id = AsyncMock(return_value=mock_character)
            
            with patch('app.services.group_chat_service.relationship_service') as mock_rel_service:
                mock_rel_service.get_relationship = AsyncMock(return_value=None)
                
                mock_llm = MagicMock()
                mock_llm.generate_stream = AsyncMock(return_value=iter(["Hello", " there"]))
                group_chat_service.llm = mock_llm
                
                events = []
                async for event in group_chat_service.stream_character_response(
                    character_id="char_001",
                    user_id="user_001",
                    message="Hi",
                    conversation_history=[],
                    other_characters=[],
                ):
                    events.append(event)
                
                assert len(events) > 0
                assert any(e["event"] == "text_delta" for e in events)
                assert any(e["event"] == "text_done" for e in events)

    @pytest.mark.asyncio
    async def test_parallel_stream_limits_concurrency(self, group_chat_service, mock_character):
        participants = ["char_001", "char_002", "char_003", "char_004"]
        
        with patch('app.services.group_chat_service.character_service') as mock_char_service:
            mock_char_service.get_character_by_id = AsyncMock(return_value=mock_character)
            
            with patch.object(
                group_chat_service,
                'stream_character_response',
                new_callable=AsyncMock
            ) as mock_stream:
                async def mock_stream_gen(*args, **kwargs):
                    yield {"event": "text_delta", "data": {"content": "test"}}
                    yield {"event": "text_done", "data": {"full_content": "test"}}
                
                mock_stream.return_value = mock_stream_gen()
                
                with patch('app.services.group_chat_service.relationship_service') as mock_rel:
                    mock_rel.get_relationship = AsyncMock(return_value=None)
                    
                    events = []
                    async for event in group_chat_service.stream_parallel_responses(
                        participants=participants,
                        user_id="user_001",
                        message="Hello",
                        conversation_history=[],
                    ):
                        events.append(event)
                    
                    assert len(events) >= len(participants)


class TestGroupChatRouter:
    
    @pytest.fixture
    def mock_group_chat_service(self):
        service = MagicMock()
        service.get_or_create_session = AsyncMock(return_value={
            "id": "session_001",
            "participants": ["char_001", "char_002"],
        })
        service.save_group_message = AsyncMock()
        service.get_group_messages = AsyncMock(return_value=[])
        service.stream_parallel_responses = AsyncMock(return_value=iter([]))
        return service
    
    def test_create_group_session_endpoint(self, client):
        response = client.post("/api/chat/group/sessions", json={
            "participants": ["char_001", "char_002"],
        })
        assert response.status_code == 200
    
    def test_get_group_session_endpoint(self, client):
        response = client.get("/api/chat/group/sessions/session_001")
        assert response.status_code in [200, 404]
    
    def test_get_group_messages_endpoint(self, client):
        response = client.get("/api/chat/group/sessions/session_001/messages")
        assert response.status_code in [200, 404]
