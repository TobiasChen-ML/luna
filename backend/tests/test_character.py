import pytest
from fastapi.testclient import TestClient


class TestCharacterRouter:
    
    def test_get_official_characters(self, client: TestClient):
        response = client.get("/api/characters/official")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_official_character(self, client: TestClient):
        response = client.get("/api/characters/official/official_001")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
    
    def test_create_character(self, client: TestClient):
        response = client.post("/api/characters", json={
            "name": "Test Character",
            "slug": "test-character",
            "description": "A test character",
            "personality": "Friendly and helpful",
            "tags": ["test", "demo"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == "Test Character"
    
    def test_get_characters(self, client: TestClient):
        response = client.get("/api/characters")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_character(self, client: TestClient, mock_character_id: str):
        response = client.get(f"/api/characters/{mock_character_id}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
    
    def test_update_character(self, client: TestClient, mock_character_id: str):
        response = client.put(f"/api/characters/{mock_character_id}", json={
            "name": "Updated Character",
            "description": "Updated description"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_delete_character(self, client: TestClient, mock_character_id: str):
        response = client.delete(f"/api/characters/{mock_character_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_categories(self, client: TestClient):
        response = client.get("/api/characters/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_discover_characters(self, client: TestClient):
        response = client.get("/api/characters/discover")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_character_by_slug(self, client: TestClient):
        response = client.get("/api/characters/by-slug/test-character")
        assert response.status_code == 200
        data = response.json()
        assert "slug" in data
    
    def test_import_character(self, client: TestClient):
        response = client.post("/api/characters/import", json={
            "name": "Imported Character",
            "slug": "imported-character",
            "description": "Imported from external source"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_export_character(self, client: TestClient, mock_character_id: str):
        response = client.get(f"/api/characters/{mock_character_id}/export")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_sync_factory(self, client: TestClient, mock_character_id: str):
        response = client.post(f"/api/characters/{mock_character_id}/sync-factory")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_force_routing(self, client: TestClient, mock_character_id: str):
        response = client.post(f"/api/characters/{mock_character_id}/force-routing", json={
            "routing_config": {"model": "advanced"}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_routing_templates(self, client: TestClient):
        response = client.get("/api/characters/force-routing/templates")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_train_lora(self, client: TestClient, mock_character_id: str):
        response = client.post(f"/api/characters/{mock_character_id}/train-lora")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "status" in data
    
    def test_get_lora_status(self, client: TestClient, mock_character_id: str):
        response = client.get(f"/api/characters/{mock_character_id}/lora-status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_lock_relationship(self, client: TestClient, mock_character_id: str):
        response = client.post(f"/api/characters/{mock_character_id}/lock-relationship")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_preview_voice(self, client: TestClient):
        response = client.post("/api/characters/voice/preview", json={
            "text": "Hello, this is a test.",
            "character_id": "char_001"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_get_voice_preview(self, client: TestClient, mock_task_id: str):
        response = client.get(f"/api/characters/voice/preview/{mock_task_id}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
