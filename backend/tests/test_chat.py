import pytest
from fastapi.testclient import TestClient


class TestChatRouter:
    
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
    
    def test_guest_send(self, client: TestClient):
        response = client.post("/api/chat/guest/send", json={
            "character_id": "char_001",
            "message": "Hello!"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_guest_audio_generate(self, client: TestClient):
        response = client.post("/api/chat/guest/audio/generate", json={
            "text": "Hello, how are you?"
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
