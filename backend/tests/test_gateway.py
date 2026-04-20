import pytest
from fastapi.testclient import TestClient


class TestGatewayRouter:
    
    def test_chat_completions(self, client: TestClient):
        response = client.post("/api/novita/chat/completions", json={
            "model": "llama-3",
            "messages": [{"role": "user", "content": "Hello"}]
        })
        assert response.status_code == 200
        data = response.json()
        assert "choices" in data
    
    def test_chat_character(self, client: TestClient):
        response = client.post("/api/novita/chat/character", json={
            "character_id": "char_001",
            "message": "Hello"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data or "response" in data
    
    def test_images_hunyuan(self, client: TestClient):
        response = client.post("/api/novita/images/hunyuan", json={
            "prompt": "A beautiful landscape"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_get_task_result(self, client: TestClient, mock_task_id: str):
        response = client.get(f"/api/novita/task-result/{mock_task_id}")
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data or "status" in data
    
    def test_images_hunyuan_wait(self, client: TestClient):
        response = client.post("/api/novita/images/hunyuan/wait", json={
            "prompt": "Test image"
        })
        assert response.status_code == 200
        data = response.json()
        assert "status" in data or "image_url" in data


class TestGatewayAdvancedRouter:
    
    def test_advanced_completions(self, client: TestClient):
        response = client.post("/api/novita-advanced/chat/completions", json={
            "model": "advanced-model",
            "messages": [{"role": "user", "content": "Hello"}]
        })
        assert response.status_code == 200
        data = response.json()
        assert "choices" in data
    
    def test_advanced_multimodal(self, client: TestClient):
        response = client.post("/api/novita-advanced/chat/multimodal", json={
            "messages": [{"role": "user", "content": "Describe this image", "image": "url"}]
        })
        assert response.status_code == 200
        data = response.json()
        assert "response" in data or "id" in data
    
    def test_advanced_function_calling(self, client: TestClient):
        response = client.post("/api/novita-advanced/chat/function-calling", json={
            "messages": [{"role": "user", "content": "What's the weather?"}],
            "functions": [{"name": "get_weather", "parameters": {}}]
        })
        assert response.status_code == 200
        data = response.json()
        assert "function_call" in data or "choices" in data
