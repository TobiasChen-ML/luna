import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.routers.chat import _compose_script_opening
from app.services.prompt_builder import PromptBuilder, PromptContext


class TestChatRouter:
    
    def test_script_opening_leads_instead_of_asking_user_for_topic(self):
        opening = _compose_script_opening(
            character_name="Roxy",
            personality="curious and warm",
            opening_line="The observatory lights flicker as Roxy turns toward you.",
            opening_scene="A storm rolls over the mountain dome.",
            world_setting="a secret mountain observatory",
            user_role="the visiting researcher",
        )

        assert "Roxy will lead" in opening
        assert "Start by telling me" not in opening
        assert "what kind of moment" not in opening
        assert "what you do first" not in opening
    
    @pytest.mark.asyncio
    async def test_script_prompt_instructs_character_to_drive_next_beat(self):
        builder = PromptBuilder()
        ctx = PromptContext(
            character_id="char_001",
            character_name="Roxy",
            script_id="script_lib_cosmos",
            use_script_library=True,
        )

        with patch(
            "app.services.prompt_builder.prompt_template_service.render_template",
            AsyncMock(return_value="Rendered section"),
        ):
            prompt = await builder.build_system_prompt(ctx)

        assert "## Story Leadership Rules" in prompt
        assert "actively open and steer the conversation" in prompt
        assert "Do not ask the user to choose a topic" in prompt
        assert "next concrete story beat" in prompt

    @pytest.mark.asyncio
    async def test_prompt_includes_character_tool_availability_rules(self):
        builder = PromptBuilder()
        ctx = PromptContext(
            character_id="char_001",
            character_name="Roxy",
        )

        with patch(
            "app.services.prompt_builder.prompt_template_service.render_template",
            AsyncMock(return_value="Rendered section"),
        ):
            prompt = await builder.build_system_prompt(ctx)

        assert "Image, video, and voice generation are available system tools" in prompt
        assert "Do not refuse ordinary media requests" in prompt
    
    def test_get_sessions(self, client: TestClient):
        response = client.get("/api/chat/sessions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "sessions" in data
    
    def test_create_session(self, client: TestClient):
        response = client.post("/api/chat/sessions", json={
            "character_id": "char_001"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "character_id" in data
    
    def test_get_session(self, client: TestClient, mock_session_id: str):
        response = client.get(f"/api/chat/sessions/{mock_session_id}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_update_session_style(self, client: TestClient, mock_session_id: str):
        response = client.patch(f"/api/chat/sessions/{mock_session_id}/style", json={
            "style": "romantic"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_update_session_context(self, client: TestClient, mock_session_id: str):
        response = client.patch(f"/api/chat/sessions/{mock_session_id}/context", json={
            "mood": "happy"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_session_messages(self, client: TestClient, mock_session_id: str):
        response = client.get(f"/api/chat/sessions/{mock_session_id}/messages")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "messages" in data
    
    def test_initialize_session(self, client: TestClient):
        response = client.post("/api/chat/sessions/initialize", json={
            "character_id": "char_001"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_start_official_chat(self, client: TestClient):
        response = client.post("/api/chat/start_official/official_001")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_chat_now_official(self, client: TestClient):
        response = client.post("/api/chat/chat_now_official/official_001")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_get_guest_credits(self, client: TestClient):
        response = client.get("/api/chat/guest/credits")
        assert response.status_code == 200
        data = response.json()
        assert "credits" in data
    
    def test_guest_send(self, client: TestClient, mock_character_id: str):
        response = client.post("/api/chat/guest/send", json={
            "character_id": mock_character_id,
            "message": "Hello!"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data.get("content"), str)
    
    def test_guest_audio_generate(self, client: TestClient):
        with patch(
            "app.routers.chat.character_service.get_character_by_id",
            AsyncMock(return_value={"id": "char_001", "voice_id": "voice_001"}),
        ):
            with patch(
                "app.routers.chat.VoiceService.generate_tts",
                AsyncMock(return_value={"audio_url": "https://example.com/audio.mp3", "duration": 1.2}),
            ):
                response = client.post("/api/chat/guest/audio/generate", json={
                    "text": "Hello, how are you?",
                    "character_id": "char_001",
                })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_request_voice_note(self, client: TestClient):
        response = client.post("/api/chat/request-voice-note", json={
            "session_id": "session_001",
            "message_id": "msg_001"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_add_message_audio(self, client: TestClient):
        response = client.post("/api/chat/messages/msg_001/audio", json={
            "audio_url": "https://example.com/audio.mp3"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_character_gallery(self, client: TestClient, mock_character_id: str):
        response = client.get(f"/api/chat/gallery/{mock_character_id}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_gallery(self, client: TestClient):
        response = client.get("/api/chat/gallery")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_animate_image(self, client: TestClient):
        response = client.post("/api/chat/animate-image", json={
            "image_url": "https://example.com/image.png"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_complete_text(self, client: TestClient):
        response = client.post("/api/chat/complete-text", json={
            "character_id": "char_001",
            "messages": [{"role": "user", "content": "Hello"}]
        })
        assert response.status_code == 200
        data = response.json()
        assert "text" in data
    
    def test_send_message(self, client: TestClient):
        response = client.post("/api/chat/message", json={
            "session_id": "session_001",
            "content": "Hello!"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_chat_send(self, client: TestClient):
        response = client.post("/api/chat/send", json={
            "character_id": "char_001",
            "message": "Hello!"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
