import pytest
from fastapi.testclient import TestClient


class TestStateRouter:
    
    def test_set_relationship_consent(self, client: TestClient, mock_character_id: str):
        response = client.post(f"/api/relationship/{mock_character_id}/consent", json={
            "consent_type": "dating",
            "granted": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_relationship(self, client: TestClient, mock_character_id: str):
        response = client.get(f"/api/relationship/{mock_character_id}")
        assert response.status_code == 200
        data = response.json()
        assert "character_id" in data
    
    def test_get_visual_permissions(self, client: TestClient, mock_character_id: str):
        response = client.get(f"/api/relationship/{mock_character_id}/visual-permissions")
        assert response.status_code == 200
        data = response.json()
        assert "character_id" in data or "permissions" in data
    
    def test_get_context(self, client: TestClient, mock_character_id: str):
        response = client.get(f"/api/context/{mock_character_id}")
        assert response.status_code == 200
        data = response.json()
        assert "character_id" in data
    
    def test_get_context_memory(self, client: TestClient, mock_character_id: str):
        response = client.get(f"/api/context/{mock_character_id}/memory")
        assert response.status_code == 200
        data = response.json()
        assert "character_id" in data or "memories" in data
    
    def test_forget_memory(self, client: TestClient, mock_character_id: str):
        response = client.post(f"/api/context/{mock_character_id}/memory/forget", json={
            "memory_ids": ["mem_001", "mem_002"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_correct_memory(self, client: TestClient, mock_character_id: str):
        response = client.post(f"/api/context/{mock_character_id}/memory/correct", json={
            "old_memory": "Wrong memory",
            "new_memory": "Corrected memory"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
