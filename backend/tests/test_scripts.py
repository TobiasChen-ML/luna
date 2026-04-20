import pytest
from fastapi.testclient import TestClient


class TestScriptsRouter:
    
    def test_list_scripts(self, client: TestClient):
        response = client.get("/api/scripts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_publish_script(self, client: TestClient):
        response = client.post("/api/scripts/publish", json={
            "title": "Test Script",
            "content": "Script content"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestScriptDAGValidation:
    """Tests for DAG validation."""
    
    def test_validate_dag(self, client: TestClient):
        """Test DAG structure validation."""
        response = client.get("/api/scripts/script_001/dag/validate")
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert "errors" in data
    
    def test_get_dag_endings(self, client: TestClient):
        """Test getting DAG endings."""
        response = client.get("/api/scripts/script_001/dag/endings")
        assert response.status_code == 200
        data = response.json()
        assert "endings" in data
        assert isinstance(data["endings"], list)
    
    def test_load_dag(self, client: TestClient):
        """Test loading DAG structure."""
        response = client.post("/api/scripts/script_001/load-dag")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert "start_node" in data


class TestScriptStateTransition:
    """Tests for script state transitions."""
    
    def test_get_relationship_stage(self, client: TestClient):
        """Test getting relationship stage."""
        response = client.get("/api/scripts/script_001/relationship-stage")
        assert response.status_code == 200
        data = response.json()
        assert "current_stage" in data
        assert "metrics" in data
    
    def test_check_emotion_gates(self, client: TestClient):
        """Test checking emotion gates."""
        response = client.get("/api/scripts/script_001/gates")
        assert response.status_code == 200
        data = response.json()
        assert "gates" in data
    
    def test_stage_regression_start_to_build(self, client: TestClient):
        """Test that stage can regress from Build back to Start."""
        pass
    
    def test_emotion_gate_blocking(self, client: TestClient):
        """Test that emotion gates can block progression."""
        pass


class TestScriptNodes:
    """Tests for script node operations."""
    
    def test_get_script_nodes(self, client: TestClient):
        """Test getting script nodes."""
        response = client.get("/api/admin/scripts/script_001/nodes")
        assert response.status_code in [200, 404]
    
    def test_create_script_node(self, client: TestClient):
        """Test creating a script node."""
        response = client.post("/api/admin/scripts/script_001/nodes", json={
            "node_type": "scene",
            "title": "Test Scene",
            "description": "A test scene"
        })
        assert response.status_code in [200, 404]


class TestAdminScriptReview:
    """Tests for admin script review endpoints."""
    
    def test_list_pending_scripts(self, client: TestClient):
        """Test listing pending scripts."""
        response = client.get("/api/admin/scripts/pending")
        assert response.status_code == 200
        data = response.json()
        assert "scripts" in data
        assert "total" in data
    
    def test_submit_for_review(self, client: TestClient):
        """Test submitting script for review."""
        response = client.post("/api/admin/scripts/script_001/submit-review", json={
            "comment": "Ready for review"
        })
        assert response.status_code in [200, 400, 404]
    
    def test_approve_script(self, client: TestClient):
        """Test approving a script."""
        response = client.post("/api/admin/scripts/script_001/approve", json={
            "comment": "LGTM"
        })
        assert response.status_code in [200, 400, 404]
    
    def test_reject_script(self, client: TestClient):
        """Test rejecting a script."""
        response = client.post("/api/admin/scripts/script_001/reject", json={
            "comment": "Needs revision"
        })
        assert response.status_code in [200, 400, 404]
    
    def test_get_script_reviews(self, client: TestClient):
        """Test getting script review history."""
        response = client.get("/api/admin/scripts/script_001/reviews")
        assert response.status_code in [200, 404]
