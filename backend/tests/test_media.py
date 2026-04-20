import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.media import ImageGenerationResult


class TestMediaRouter:
    
    def test_generate_image_async(self, client: TestClient):
        response = client.post("/api/images/generate-async", json={
            "prompt": "A beautiful sunset",
            "width": 512,
            "height": 512
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "status" in data
    
    def test_generate_image(self, client: TestClient):
        response = client.post("/api/images/generate", json={
            "prompt": "A beautiful sunset"
        })
        assert response.status_code == 200
        data = response.json()
        assert "image_url" in data
    
    def test_generate_batch(self, client: TestClient):
        response = client.post("/api/images/generate-batch", json={
            "prompts": ["Sunset", "Sunrise"],
            "width": 512,
            "height": 512
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_suggestion_previews(self, client: TestClient):
        response = client.post("/api/images/suggestion-previews", json={
            "character_id": "char_001",
            "count": 4
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_generate_preset(self, client: TestClient):
        response = client.post("/api/images/generate-preset", json={
            "preset": "fantasy"
        })
        assert response.status_code == 200
        data = response.json()
        assert "image_url" in data
    
    def test_get_preset_characters(self, client: TestClient):
        response = client.get("/api/images/preset-characters")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_preset_by_character(self, client: TestClient):
        response = client.get("/api/images/generate-preset/CharacterName")
        assert response.status_code == 200
        data = response.json()
        assert "character_name" in data
    
    def test_generate_and_save(self, client: TestClient):
        response = client.post("/api/images/generate-and-save", json={
            "prompt": "Test image"
        })
        assert response.status_code == 200
        data = response.json()
        assert "image_url" in data
    
    def test_generate_preset_and_save(self, client: TestClient):
        response = client.post("/api/images/generate-preset-and-save", json={
            "preset": "fantasy"
        })
        assert response.status_code == 200
        data = response.json()
        assert "image_url" in data
    
    def test_animate_direct(self, client: TestClient):
        response = client.post("/api/images/animate-direct", json={
            "image_url": "https://example.com/image.png"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_animate_message(self, client: TestClient):
        response = client.post("/api/images/messages/msg_001/animate", json={
            "style": "default"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_generate_with_character(self, client: TestClient):
        response = client.post("/api/images/generate-with-character/char_001", json={
            "prompt": "Character in a forest"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_animate_standalone(self, client: TestClient):
        from app.services.media import NovitaVideoProvider
        
        mock_provider = MagicMock(spec=NovitaVideoProvider)
        mock_provider.generate_video_async = AsyncMock(return_value="task_animate_mocked")
        
        with patch("app.routers.media.media_service.get_video_provider", return_value=mock_provider):
            response = client.post("/api/images/animate-standalone", json={
                "image_url": "https://example.com/image.png"
            })
            assert response.status_code == 200
            data = response.json()
            assert "task_id" in data
    
    def test_get_task(self, client: TestClient, mock_task_id: str):
        response = client.get(f"/api/images/tasks/{mock_task_id}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_generate_video_wan(self, client: TestClient):
        response = client.post("/api/images/generate-video-wan-character", json={
            "character_id": "char_001",
            "prompt": "Character walking"
        })
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
    
    def test_save_media(self, client: TestClient):
        response = client.post("/api/images/save-media", json={
            "url": "https://example.com/image.png",
            "type": "image"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_my_media(self, client: TestClient):
        response = client.get("/api/images/my-media")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_generate_voice_token(self, client: TestClient):
        response = client.post("/api/images/voice/generate_token")
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
    
    def test_generate_message_audio(self, client: TestClient):
        response = client.post("/api/images/voice/messages/msg_001/audio", json={
            "text": "Hello world"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_request_voice_note(self, client: TestClient):
        response = client.post("/api/images/voice/request-note", json={
            "character_id": "char_001",
            "text": "Voice note text"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_novita_callback(self, client: TestClient):
        response = client.post("/api/images/callbacks/novita", json={
            "task_id": "task_001",
            "status": "completed"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_media_callback(self, client: TestClient):
        response = client.post("/api/images/callbacks/media", json={
            "task_id": "task_001"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_callbacks_health(self, client: TestClient):
        response = client.get("/api/images/callbacks/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
