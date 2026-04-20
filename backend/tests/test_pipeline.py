import pytest
from fastapi.testclient import TestClient


class TestPipelineRouter:
    
    def test_get_user_events(self, client: TestClient):
        response = client.get("/api/pipeline/events/user")
        assert response.status_code == 200
    
    def test_get_session_events(self, client: TestClient, mock_session_id: str):
        response = client.get(f"/api/pipeline/events/session/{mock_session_id}")
        assert response.status_code == 200
    
    def test_generate_audio(self, client: TestClient):
        response = client.post("/api/pipeline/generate/audio", json={
            "text": "Hello world",
            "voice_id": "voice_001"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_generate_multimodal(self, client: TestClient):
        response = client.post("/api/pipeline/generate/multimodal", json={
            "text": "Generate image from text",
            "type": "image"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_internal_publish(self, client: TestClient):
        response = client.post("/api/pipeline/internal/publish", json={
            "content_id": "content_001",
            "type": "character"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
