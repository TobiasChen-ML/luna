import pytest
from fastapi.testclient import TestClient


class TestUGCRouter:
    
    def test_get_character_quota(self, client: TestClient):
        response = client.get("/api/ugc/characters/quota")
        assert response.status_code == 200
        data = response.json()
        assert "used" in data or "limit" in data
    
    def test_create_ugc_character(self, client: TestClient):
        response = client.post("/api/ugc/characters", json={
            "name": "UGC Character",
            "description": "User created character"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_list_ugc_characters(self, client: TestClient):
        response = client.get("/api/ugc/characters")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_update_ugc_character(self, client: TestClient):
        response = client.put("/api/ugc/characters/char_001", json={
            "name": "Updated UGC Character"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_delete_ugc_character(self, client: TestClient):
        response = client.delete("/api/ugc/characters/char_001")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_publish_ugc_character(self, client: TestClient):
        response = client.post("/api/ugc/characters/char_001/publish")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_fork_ugc_character(self, client: TestClient):
        response = client.post("/api/ugc/characters/char_001/fork")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_list_community_characters(self, client: TestClient):
        response = client.get("/api/ugc/community/characters")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_script_quota(self, client: TestClient):
        response = client.get("/api/ugc/scripts/quota")
        assert response.status_code == 200
        data = response.json()
        assert "used" in data or "limit" in data
    
    def test_get_script_templates(self, client: TestClient):
        response = client.get("/api/ugc/scripts/templates")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_script_from_template(self, client: TestClient):
        response = client.post("/api/ugc/scripts/from-template", json={
            "template_id": "template_001",
            "title": "My Script"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_create_custom_script(self, client: TestClient):
        response = client.post("/api/ugc/scripts/custom", json={
            "title": "Custom Script",
            "content": "Script content here"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_update_ugc_script(self, client: TestClient):
        response = client.put("/api/ugc/scripts/script_001", json={
            "title": "Updated Script",
            "content": "Updated content"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_delete_ugc_script(self, client: TestClient):
        response = client.delete("/api/ugc/scripts/script_001")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_publish_ugc_script(self, client: TestClient):
        response = client.post("/api/ugc/scripts/script_001/publish")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_list_community_scripts(self, client: TestClient):
        response = client.get("/api/ugc/community/scripts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_creator_overview(self, client: TestClient):
        response = client.get("/api/ugc/creator/overview")
        assert response.status_code == 200
        data = response.json()
        assert "creator_id" in data or "stats" in data
