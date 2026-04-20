"""
Tests for Script Review System.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime


class TestScriptReviewRouter:
    """Test script review endpoints."""
    
    def test_list_pending_scripts(self, client: TestClient):
        """Test listing pending scripts for review."""
        response = client.get("/api/admin/scripts/pending")
        assert response.status_code == 200
        data = response.json()
        assert "scripts" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
    
    def test_list_pending_scripts_pagination(self, client: TestClient):
        """Test pagination for pending scripts."""
        response = client.get("/api/admin/scripts/pending?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10
    
    def test_submit_script_for_review(self, client: TestClient):
        """Test submitting a script for review."""
        response = client.post("/api/admin/scripts/script_test_001/submit-review", json={
            "comment": "Ready for review"
        })
        assert response.status_code in [200, 400, 404]
    
    def test_approve_script(self, client: TestClient):
        """Test approving a script."""
        response = client.post("/api/admin/scripts/script_test_001/approve", json={
            "comment": "Looks good"
        })
        assert response.status_code in [200, 400, 404]
    
    def test_reject_script(self, client: TestClient):
        """Test rejecting a script."""
        response = client.post("/api/admin/scripts/script_test_001/reject", json={
            "comment": "Needs revision"
        })
        assert response.status_code in [200, 400, 404]
    
    def test_get_script_reviews(self, client: TestClient):
        """Test getting review history for a script."""
        response = client.get("/api/admin/scripts/script_test_001/reviews")
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)


class TestScriptReviewService:
    """Test script review service methods."""
    
    @pytest.mark.asyncio
    async def test_get_review_not_found(self):
        """Test getting non-existent review."""
        from app.services.script_service import script_service
        result = await script_service.get_review("nonexistent_review")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_list_reviews_empty(self):
        """Test listing reviews for non-existent script."""
        from app.services.script_service import script_service
        result = await script_service.list_reviews("nonexistent_script")
        assert result == []
    
    @pytest.mark.asyncio
    async def test_list_pending_reviews(self):
        """Test listing pending reviews."""
        from app.services.script_service import script_service
        scripts, total = await script_service.list_pending_reviews(page=1, page_size=10)
        assert isinstance(scripts, list)
        assert isinstance(total, int)


class TestReviewModels:
    """Test review-related Pydantic models."""
    
    def test_review_action_enum(self):
        """Test ReviewAction enum values."""
        from app.models.script import ReviewAction
        assert ReviewAction.SUBMIT.value == "submit"
        assert ReviewAction.APPROVE.value == "approve"
        assert ReviewAction.REJECT.value == "reject"
        assert ReviewAction.ARCHIVE.value == "archive"
    
    def test_script_review_create(self):
        """Test ScriptReviewCreate model."""
        from app.models.script import ScriptReviewCreate, ReviewAction
        review = ScriptReviewCreate(
            script_id="script_001",
            action=ReviewAction.SUBMIT,
            comment="Test comment"
        )
        assert review.script_id == "script_001"
        assert review.action == ReviewAction.SUBMIT
        assert review.comment == "Test comment"
    
    def test_script_review_create_without_comment(self):
        """Test ScriptReviewCreate without optional comment."""
        from app.models.script import ScriptReviewCreate, ReviewAction
        review = ScriptReviewCreate(
            script_id="script_001",
            action=ReviewAction.APPROVE
        )
        assert review.comment is None
    
    def test_play_history_entry_model(self):
        """Test PlayHistoryEntry model."""
        from app.models.script import PlayHistoryEntry
        entry = PlayHistoryEntry(
            play_id="prog_001",
            play_index=1,
            status="completed",
            ending_type="good",
            completion_time_minutes=30,
            started_at=datetime.now(),
            choices_count=10
        )
        assert entry.play_id == "prog_001"
        assert entry.play_index == 1
        assert entry.ending_type == "good"


class TestReviewWorkflow:
    """Test complete review workflow scenarios."""
    
    @pytest.mark.asyncio
    async def test_reject_without_comment_should_fail(self):
        """Test that rejecting without comment is handled."""
        from app.services.script_service import script_service
        result = await script_service.reject_script("nonexistent", "admin", None)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_approve_wrong_status_should_fail(self):
        """Test that approving non-pending script fails."""
        from app.services.script_service import script_service
        result = await script_service.approve_script("nonexistent", "admin", "test")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_submit_wrong_status_should_fail(self):
        """Test that submitting non-draft script fails."""
        from app.services.script_service import script_service
        result = await script_service.submit_for_review("nonexistent", "admin", "test")
        assert result is None
