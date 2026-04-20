import pytest
from fastapi.testclient import TestClient


class TestStoryRouter:
    
    def test_get_available_stories(self, client: TestClient):
        response = client.get("/api/stories/available/char_001")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_character_stories(self, client: TestClient):
        response = client.get("/api/stories/character/char_001")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_story(self, client: TestClient, mock_story_id: str):
        response = client.get(f"/api/stories/{mock_story_id}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_get_story_nodes(self, client: TestClient, mock_story_id: str):
        response = client.get(f"/api/stories/{mock_story_id}/nodes")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_start_story(self, client: TestClient, mock_story_id: str):
        response = client.post(f"/api/stories/{mock_story_id}/start")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_resume_story(self, client: TestClient, mock_story_id: str):
        response = client.post(f"/api/stories/{mock_story_id}/resume")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_make_story_choice(self, client: TestClient, mock_story_id: str):
        response = client.post(f"/api/stories/{mock_story_id}/choice", json={
            "choice_id": "choice_001"
        })
        assert response.status_code == 200
        data = response.json()
        assert "story_id" in data or "next_node_id" in data
    
    def test_get_story_progress(self, client: TestClient):
        response = client.get("/api/stories/progress/char_001")
        assert response.status_code == 200
        data = response.json()
        assert "character_id" in data
    
    def test_generate_storyboard(self, client: TestClient, mock_story_id: str):
        response = client.post(f"/api/stories/{mock_story_id}/storyboard/generate")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_create_story(self, client: TestClient):
        response = client.post("/api/stories", json={
            "title": "New Story",
            "character_id": "char_001"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_update_story(self, client: TestClient, mock_story_id: str):
        response = client.put(f"/api/stories/{mock_story_id}", json={
            "title": "Updated Story"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_delete_story(self, client: TestClient, mock_story_id: str):
        response = client.delete(f"/api/stories/{mock_story_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_create_story_node(self, client: TestClient, mock_story_id: str):
        response = client.post(f"/api/stories/{mock_story_id}/nodes", json={
            "content": "Node content"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_update_story_node(self, client: TestClient):
        response = client.put("/api/stories/nodes/node_001", json={
            "content": "Updated content"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_delete_story_node(self, client: TestClient):
        response = client.delete("/api/stories/nodes/node_001")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestStoryAdminRouter:
    
    def test_admin_create_story(self, client: TestClient):
        response = client.post("/api/stories/admin/create", json={
            "title": "Admin Story",
            "character_id": "char_001"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_admin_update_story(self, client: TestClient):
        response = client.put("/api/stories/admin/story_001", json={
            "title": "Admin Updated"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_admin_delete_story(self, client: TestClient):
        response = client.delete("/api/stories/admin/story_001")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
