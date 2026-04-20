import pytest
from fastapi.testclient import TestClient


class TestWorldCharacterRouter:
    
    def test_get_official_characters(self, client: TestClient):
        response = client.get("/api/world/characters/official")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_official_character(self, client: TestClient):
        response = client.get("/api/world/characters/official/official_001")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_create_character(self, client: TestClient):
        response = client.post("/api/world/characters", json={
            "name": "World Character",
            "slug": "world-character"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_get_characters(self, client: TestClient):
        response = client.get("/api/world/characters")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_character(self, client: TestClient):
        response = client.get("/api/world/characters/char_001")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_update_character(self, client: TestClient):
        response = client.put("/api/world/characters/char_001", json={
            "name": "Updated"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_delete_character(self, client: TestClient):
        response = client.delete("/api/world/characters/char_001")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_categories(self, client: TestClient):
        response = client.get("/api/world/characters/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_discover_characters(self, client: TestClient):
        response = client.get("/api/world/characters/discover")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_character_by_slug(self, client: TestClient):
        response = client.get("/api/world/characters/by-slug/test-character")
        assert response.status_code == 200
        data = response.json()
        assert "slug" in data
    
    def test_lock_relationship(self, client: TestClient):
        response = client.post("/api/world/characters/char_001/lock-relationship")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_force_routing(self, client: TestClient):
        response = client.post("/api/world/characters/char_001/force-routing", json={
            "config": "advanced"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_routing_templates(self, client: TestClient):
        response = client.get("/api/world/characters/force-routing/templates")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_export_character(self, client: TestClient):
        response = client.get("/api/world/characters/char_001/export")
        assert response.status_code == 200
    
    def test_import_character(self, client: TestClient):
        response = client.post("/api/world/characters/import", json={
            "name": "Imported"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_train_lora(self, client: TestClient):
        response = client.post("/api/world/characters/char_001/train-lora")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_get_lora_status(self, client: TestClient):
        response = client.get("/api/world/characters/char_001/lora-status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_sync_factory(self, client: TestClient):
        response = client.post("/api/world/characters/char_001/sync-factory")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_preview_voice(self, client: TestClient):
        response = client.post("/api/world/characters/voice/preview", json={
            "text": "Test"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_get_voice_preview(self, client: TestClient):
        response = client.get("/api/world/characters/voice/preview/task_001")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data


class TestWorldStoryRouter:
    
    def test_get_available_stories(self, client: TestClient):
        response = client.get("/api/world/stories/available/char_001")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_character_stories(self, client: TestClient):
        response = client.get("/api/world/stories/character/char_001")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_story(self, client: TestClient):
        response = client.get("/api/world/stories/story_001")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_get_story_nodes(self, client: TestClient):
        response = client.get("/api/world/stories/story_001/nodes")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_start_story(self, client: TestClient):
        response = client.post("/api/world/stories/story_001/start")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_resume_story(self, client: TestClient):
        response = client.post("/api/world/stories/story_001/resume")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_make_choice(self, client: TestClient):
        response = client.post("/api/world/stories/story_001/choice", json={
            "choice": "A"
        })
        assert response.status_code == 200
    
    def test_get_progress(self, client: TestClient):
        response = client.get("/api/world/stories/progress/char_001")
        assert response.status_code == 200
        data = response.json()
        assert "character_id" in data
    
    def test_generate_storyboard(self, client: TestClient):
        response = client.post("/api/world/stories/story_001/storyboard/generate")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_create_story(self, client: TestClient):
        response = client.post("/api/world/stories", json={
            "title": "Test",
            "character_id": "char_001"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_update_story(self, client: TestClient):
        response = client.put("/api/world/stories/story_001", json={
            "title": "Updated"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_delete_story(self, client: TestClient):
        response = client.delete("/api/world/stories/story_001")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_create_node(self, client: TestClient):
        response = client.post("/api/world/stories/story_001/nodes", json={
            "content": "Node"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_update_node(self, client: TestClient):
        response = client.put("/api/world/stories/nodes/node_001", json={
            "content": "Updated"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_delete_node(self, client: TestClient):
        response = client.delete("/api/world/stories/nodes/node_001")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_admin_create_story(self, client: TestClient):
        response = client.post("/api/world/stories/admin/create", json={
            "title": "Admin Story",
            "character_id": "char_001"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_admin_update_story(self, client: TestClient):
        response = client.put("/api/world/stories/admin/story_001", json={
            "title": "Updated"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_admin_delete_story(self, client: TestClient):
        response = client.delete("/api/world/stories/admin/story_001")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestWorldContextRouter:
    
    def test_get_context(self, client: TestClient):
        response = client.get("/api/context/char_001")
        assert response.status_code == 200
        data = response.json()
        assert "character_id" in data
    
    def test_get_memory(self, client: TestClient):
        response = client.get("/api/context/char_001/memory")
        assert response.status_code == 200
        data = response.json()
        assert "character_id" in data or "memories" in data
    
    def test_forget_memory(self, client: TestClient):
        response = client.post("/api/context/char_001/memory/forget", json={
            "memory_ids": ["mem_001"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_correct_memory(self, client: TestClient):
        response = client.post("/api/context/char_001/memory/correct", json={
            "old_memory": "Old",
            "new_memory": "New"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestWorldRelationshipRouter:
    
    def test_set_consent(self, client: TestClient):
        response = client.post("/api/relationship/char_001/consent", json={
            "consent_type": "dating",
            "granted": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_relationship(self, client: TestClient):
        response = client.get("/api/relationship/char_001")
        assert response.status_code == 200
        data = response.json()
        assert "character_id" in data
    
    def test_get_visual_perms(self, client: TestClient):
        response = client.get("/api/relationship/char_001/visual-permissions")
        assert response.status_code == 200
        data = response.json()
        assert "character_id" in data or "permissions" in data
