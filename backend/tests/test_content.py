import pytest
from fastapi.testclient import TestClient


class TestContentRouter:
    
    def test_get_characters(self, client: TestClient):
        response = client.get("/api/v1/characters")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_character(self, client: TestClient):
        response = client.post("/api/v1/characters", json={
            "name": "V1 Character",
            "slug": "v1-character",
            "description": "Created via v1 API"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_import_character(self, client: TestClient):
        response = client.post("/api/v1/characters/import", json={
            "name": "Imported",
            "slug": "imported"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_expand_character(self, client: TestClient):
        response = client.post("/api/v1/characters/expand", json={
            "name": "Expanded Character"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_get_character(self, client: TestClient):
        response = client.get("/api/v1/characters/char_001")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_update_character(self, client: TestClient):
        response = client.put("/api/v1/characters/char_001", json={
            "name": "Updated Name"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_delete_character(self, client: TestClient):
        response = client.delete("/api/v1/characters/char_001")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_export_character(self, client: TestClient):
        response = client.get("/api/v1/characters/char_001/export")
        assert response.status_code == 200
    
    def test_render_prompt(self, client: TestClient):
        response = client.get("/api/v1/characters/char_001/render-prompt")
        assert response.status_code == 200
        data = response.json()
        assert "system_prompt" in data or "character_id" in data
    
    def test_get_character_versions(self, client: TestClient):
        response = client.get("/api/v1/characters/family_001/versions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_set_character_voice(self, client: TestClient):
        response = client.post("/api/v1/characters/char_001/voice", json={
            "voice_id": "voice_001"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_update_lifecycle(self, client: TestClient):
        response = client.patch("/api/v1/characters/char_001/lifecycle", json={
            "status": "published"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_create_story(self, client: TestClient):
        response = client.post("/api/v1/stories", json={
            "title": "Test Story",
            "character_id": "char_001"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_get_stories(self, client: TestClient):
        response = client.get("/api/v1/stories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_story(self, client: TestClient):
        response = client.get("/api/v1/stories/story_001")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_get_story_characters(self, client: TestClient):
        response = client.get("/api/v1/stories/story_001/characters")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_add_story_character(self, client: TestClient):
        response = client.post("/api/v1/stories/story_001/characters/char_001")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_remove_story_character(self, client: TestClient):
        response = client.delete("/api/v1/stories/story_001/characters/char_001")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_create_story_async(self, client: TestClient):
        response = client.post("/api/v1/stories/async", json={
            "title": "Async Story",
            "character_id": "char_001"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "status" in data
    
    def test_index_memory(self, client: TestClient):
        response = client.post("/api/v1/memory/index", json={
            "user_id": "user_001",
            "character_id": "char_001",
            "content": "User likes coffee"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_query_memory(self, client: TestClient):
        response = client.post("/api/v1/memory/query", json={
            "query": "coffee preferences",
            "character_id": "char_001"
        })
        assert response.status_code == 200
        data = response.json()
        assert "results" in data or "total" in data
    
    def test_extract_memory(self, client: TestClient):
        response = client.post("/api/v1/memory/extract", json={
            "session_id": "session_001",
            "messages": []
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_delete_memory(self, client: TestClient):
        response = client.delete("/api/v1/memory/index/mem_001")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_memory_stats(self, client: TestClient):
        response = client.get("/api/v1/memory/stats")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_memory_health(self, client: TestClient):
        response = client.get("/api/v1/memory/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_get_prompts(self, client: TestClient):
        response = client.get("/api/v1/prompts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_prompt(self, client: TestClient):
        response = client.get("/api/v1/prompts/default")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
    
    def test_update_prompt(self, client: TestClient):
        response = client.put("/api/v1/prompts/default", json={
            "content": "Updated prompt content"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_delete_prompt(self, client: TestClient):
        response = client.delete("/api/v1/prompts/test_prompt")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_templates(self, client: TestClient):
        response = client.get("/api/v1/templates")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_template(self, client: TestClient):
        response = client.get("/api/v1/templates/template_001")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_get_categories(self, client: TestClient):
        response = client.get("/api/v1/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_collection(self, client: TestClient):
        response = client.post("/api/v1/collections", json={
            "name": "My Collection"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_collections(self, client: TestClient):
        response = client.get("/api/v1/collections")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_collection(self, client: TestClient):
        response = client.get("/api/v1/collections/col_001")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_update_collection(self, client: TestClient):
        response = client.put("/api/v1/collections/col_001", json={
            "name": "Updated Collection"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_delete_collection(self, client: TestClient):
        response = client.delete("/api/v1/collections/col_001")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_collection_characters(self, client: TestClient):
        response = client.get("/api/v1/collections/col_001/characters")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_add_to_collection(self, client: TestClient):
        response = client.post("/api/v1/collections/col_001/characters/char_001")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_remove_from_collection(self, client: TestClient):
        response = client.delete("/api/v1/collections/col_001/characters/char_001")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_task(self, client: TestClient, mock_task_id: str):
        response = client.get(f"/api/v1/tasks/{mock_task_id}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "status" in data
    
    def test_get_tasks(self, client: TestClient):
        response = client.get("/api/v1/tasks")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_text_to_speech(self, client: TestClient):
        response = client.post("/api/v1/voice/tts", json={
            "text": "Hello world",
            "character_id": "char_001"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_tts_with_presence(self, client: TestClient):
        response = client.post("/api/v1/voice/tts/with-presence", json={
            "text": "Hello world",
            "character_id": "char_001"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_voice_health(self, client: TestClient):
        response = client.get("/api/v1/voice/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
