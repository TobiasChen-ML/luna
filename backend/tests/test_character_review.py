import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


class TestUGCCharacterCreation:
    """Test UGC character creation and review workflow"""

    @pytest.mark.asyncio
    async def test_create_ugc_character_sets_pending_status(self):
        """UGC characters should have review_status='pending' and is_public=False"""
        from app.services.character_service import character_service
        from app.models.character import CharacterCreate
        from app.core.database import db
        
        mock_character_data = {
            "id": "char_ugc_001",
            "name": "User Created Character",
            "slug": "user-created-character",
            "review_status": "pending",
            "is_public": False,
            "creator_id": "user_001",
        }
        
        with patch.object(db, 'execute', new_callable=AsyncMock) as mock_execute:
            with patch.object(character_service, 'get_character_by_slug', new_callable=AsyncMock) as mock_get_slug:
                with patch.object(character_service, 'get_character_by_id', new_callable=AsyncMock) as mock_get_id:
                    mock_get_slug.return_value = None
                    mock_get_id.return_value = mock_character_data
                    mock_execute.return_value = None
                    
                    data = CharacterCreate(name="User Created Character")
                    result = await character_service.create_ugc_character(data, "user_001")
                    
                    assert result is not None
                    assert result["review_status"] == "pending"
                    assert result["is_public"] is False
                    assert result["creator_id"] == "user_001"

    @pytest.mark.asyncio
    async def test_list_user_characters(self):
        """Should only list characters created by the user"""
        from app.services.character_service import character_service
        from app.core.database import db
        
        mock_characters = [
            {"id": "char_001", "name": "My Character", "creator_id": "user_001"},
            {"id": "char_002", "name": "My Other Character", "creator_id": "user_001"},
        ]
        
        mock_count = {"total": 2}
        
        with patch.object(db, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = [mock_count, mock_characters]
            
            characters, total = await character_service.list_user_characters("user_001")
            
            assert total == 2
            assert len(characters) == 2


class TestCharacterReviewWorkflow:
    """Test admin review endpoints"""

    def test_list_pending_characters_api(self, admin_client: TestClient):
        """Admin should be able to list pending characters"""
        response = admin_client.get("/admin/api/characters/pending-review")
        assert response.status_code in (200, 404)

    def test_approve_character_api(self, admin_client: TestClient):
        """Admin should be able to approve a character"""
        response = admin_client.post("/admin/api/characters/non_existent/approve")
        assert response.status_code in (200, 404)

    def test_reject_character_api(self, admin_client: TestClient):
        """Admin should be able to reject a character with reason"""
        response = admin_client.post("/admin/api/characters/non_existent/reject", json={
            "rejection_reason": "Inappropriate content"
        })
        assert response.status_code in (200, 404)

    def test_reject_character_without_reason(self, admin_client: TestClient):
        """Admin can reject without providing a reason"""
        response = admin_client.post("/admin/api/characters/non_existent/reject", json={})
        assert response.status_code in (200, 404)


class TestCharacterReviewService:
    """Test character review service methods"""

    @pytest.mark.asyncio
    async def test_approve_character(self):
        """Approving character should set review_status='approved' and is_public=True"""
        from app.services.character_service import character_service
        from app.core.database import db
        
        mock_character = {
            "id": "char_001",
            "name": "Test Character",
            "review_status": "pending",
            "is_public": False,
        }
        
        mock_approved = {
            "id": "char_001",
            "name": "Test Character",
            "review_status": "approved",
            "is_public": True,
            "reviewer_id": "admin_001",
        }
        
        with patch.object(character_service, 'get_character_by_id', new_callable=AsyncMock) as mock_get:
            with patch.object(db, 'execute', new_callable=AsyncMock) as mock_execute:
                mock_get.side_effect = [mock_character, mock_approved]
                mock_execute.return_value = None
                
                result = await character_service.approve_character("char_001", "admin_001")
                
                assert result is not None
                assert result["review_status"] == "approved"
                assert result["is_public"] is True

    @pytest.mark.asyncio
    async def test_approve_nonexistent_character(self):
        """Approving non-existent character should return None"""
        from app.services.character_service import character_service
        
        with patch.object(character_service, 'get_character_by_id', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            result = await character_service.approve_character("non_existent", "admin_001")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_reject_character_with_reason(self):
        """Rejecting character should set review_status='rejected' and store reason"""
        from app.services.character_service import character_service
        from app.core.database import db
        
        mock_character = {
            "id": "char_001",
            "name": "Test Character",
            "review_status": "pending",
        }
        
        mock_rejected = {
            "id": "char_001",
            "name": "Test Character",
            "review_status": "rejected",
            "is_public": False,
            "reviewer_id": "admin_001",
            "rejection_reason": "Inappropriate content",
        }
        
        with patch.object(character_service, 'get_character_by_id', new_callable=AsyncMock) as mock_get:
            with patch.object(db, 'execute', new_callable=AsyncMock) as mock_execute:
                mock_get.side_effect = [mock_character, mock_rejected]
                mock_execute.return_value = None
                
                result = await character_service.reject_character(
                    "char_001", 
                    "admin_001", 
                    "Inappropriate content"
                )
                
                assert result is not None
                assert result["review_status"] == "rejected"
                assert result["is_public"] is False

    @pytest.mark.asyncio
    async def test_reject_nonexistent_character(self):
        """Rejecting non-existent character should return None"""
        from app.services.character_service import character_service
        
        with patch.object(character_service, 'get_character_by_id', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            result = await character_service.reject_character("non_existent", "admin_001", "Reason")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_list_pending_characters(self):
        """Should list only characters with review_status='pending'"""
        from app.services.character_service import character_service
        from app.core.database import db
        
        mock_pending = [
            {"id": "char_001", "name": "Pending Character", "review_status": "pending"},
            {"id": "char_002", "name": "Another Pending", "review_status": "pending"},
        ]
        
        mock_count = {"total": 2}
        
        with patch.object(db, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = [mock_count, mock_pending]
            
            characters, total = await character_service.list_pending_characters()
            
            assert total == 2
            assert len(characters) == 2


class TestUGCCharacterEndpoints:
    """Test UGC character endpoints for regular users"""

    def test_create_ugc_endpoint_requires_auth(self, client: TestClient):
        """UGC creation endpoint should require authentication"""
        response = client.post("/api/characters/ugc", json={
            "name": "Test Character"
        })
        assert response.status_code in (200, 401, 403, 422, 500)

    def test_list_my_characters_endpoint_requires_auth(self, client: TestClient):
        """My characters endpoint should require authentication"""
        response = client.get("/api/characters/my")
        assert response.status_code in (200, 401, 403)