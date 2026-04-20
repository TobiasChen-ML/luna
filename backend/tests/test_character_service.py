import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestCharacterServiceBatchDelete:
    
    @pytest.mark.asyncio
    async def test_batch_delete_empty_list(self):
        from app.services.character_service import character_service
        
        result = await character_service.batch_delete([])
        assert result == 0
    
    @pytest.mark.asyncio
    async def test_batch_delete_single_id(self):
        from app.services.character_service import character_service
        from app.core.database import db
        from app.models.character import CharacterCreate
        
        with patch.object(db, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = None
            
            result = await character_service.batch_delete(["char_001"])
            
            assert result == 1
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            assert "DELETE FROM characters WHERE id IN" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_batch_delete_multiple_ids(self):
        from app.services.character_service import character_service
        from app.core.database import db
        
        with patch.object(db, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = None
            
            result = await character_service.batch_delete(["char_001", "char_002", "char_003"])
            
            assert result == 3
            mock_execute.assert_called_once()


class TestCharacterServiceIncrementCounts:
    
    @pytest.mark.asyncio
    async def test_increment_chat_count(self):
        from app.services.character_service import character_service
        from app.core.database import db
        
        with patch.object(db, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = None
            
            await character_service.increment_chat_count("char_001")
            
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            assert "chat_count = chat_count + 1" in call_args[0][0]
            assert "char_001" in str(call_args[0][1])
    
    @pytest.mark.asyncio
    async def test_increment_view_count(self):
        from app.services.character_service import character_service
        from app.core.database import db
        
        with patch.object(db, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = None
            
            await character_service.increment_view_count("char_001")
            
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            assert "view_count = view_count + 1" in call_args[0][0]
            assert "char_001" in str(call_args[0][1])
    
    @pytest.mark.asyncio
    async def test_increment_counts_concurrent(self):
        from app.services.character_service import character_service
        from app.core.database import db
        import uuid
        
        call_count = 0
        call_lock = asyncio.Lock()
        
        async def mock_execute(*args, **kwargs):
            nonlocal call_count
            async with call_lock:
                call_count += 1
            await asyncio.sleep(0.01)
            return None
        
        with patch.object(db, 'execute', side_effect=mock_execute):
            tasks = []
            for _ in range(10):
                tasks.append(character_service.increment_chat_count("char_001"))
                tasks.append(character_service.increment_view_count("char_001"))
            
            await asyncio.gather(*tasks)
            
            assert call_count == 20


class TestCharacterServiceCreateCharacter:
    
    @pytest.mark.asyncio
    async def test_create_character_basic(self):
        from app.services.character_service import character_service
        from app.core.database import db
        from app.models.character import CharacterCreate
        
        mock_character_data = {
            "id": "char_new_001",
            "name": "Test Character",
            "slug": "test-character",
            "description": "A test character",
            "is_official": True,
            "is_public": True,
        }
        
        with patch.object(db, 'execute', new_callable=AsyncMock) as mock_execute:
            with patch.object(character_service, 'get_character_by_slug', new_callable=AsyncMock) as mock_get_slug:
                with patch.object(character_service, 'get_character_by_id', new_callable=AsyncMock) as mock_get_id:
                    mock_get_slug.return_value = None
                    mock_get_id.return_value = mock_character_data
                    mock_execute.return_value = None
                    
                    from app.models.character import CharacterCreate
                    data = CharacterCreate(
                        name="Test Character",
                        slug="test-character",
                        mature_image_url="https://example.com/mature-avatar.png",
                        mature_cover_url="https://example.com/mature-cover.png",
                        mature_video_url="https://example.com/mature-video.mp4",
                    )
                    result = await character_service.create_character(data)
                    
                    assert result is not None
                    mock_execute.assert_called()
                    sql = mock_execute.call_args[0][0]
                    params = mock_execute.call_args[0][1]
                    assert "mature_image_url" in sql
                    assert "mature_cover_url" in sql
                    assert "mature_video_url" in sql
                    assert "https://example.com/mature-avatar.png" in params
                    assert "https://example.com/mature-cover.png" in params
                    assert "https://example.com/mature-video.mp4" in params


class TestCharacterServiceUpdateCharacter:
    
    @pytest.mark.asyncio
    async def test_update_character_not_found(self):
        from app.services.character_service import character_service
        from app.models.character import CharacterUpdate
        
        with patch.object(character_service, 'get_character_by_id', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            result = await character_service.update_character("non_existent", CharacterUpdate(name="New Name"))
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_update_character_success(self):
        from app.services.character_service import character_service
        from app.models.character import CharacterUpdate
        from app.core.database import db
        
        mock_existing = {
            "id": "char_001",
            "name": "Old Name",
            "slug": "old-slug",
            "is_public": True,
        }
        
        mock_updated = {
            "id": "char_001",
            "name": "New Name",
            "slug": "old-slug",
            "is_public": True,
        }
        
        with patch.object(character_service, 'get_character_by_id', new_callable=AsyncMock) as mock_get:
            with patch.object(db, 'execute', new_callable=AsyncMock) as mock_execute:
                mock_get.side_effect = [mock_existing, mock_updated]
                mock_execute.return_value = None
                
                result = await character_service.update_character("char_001", CharacterUpdate(name="New Name"))
                
                assert result is not None
                assert result["name"] == "New Name"

    @pytest.mark.asyncio
    async def test_update_character_persists_mature_media(self):
        from app.services.character_service import character_service
        from app.models.character import CharacterUpdate
        from app.core.database import db

        mock_existing = {
            "id": "char_001",
            "name": "Old Name",
            "slug": "old-slug",
            "is_public": True,
        }

        mock_updated = {
            "id": "char_001",
            "name": "Old Name",
            "slug": "old-slug",
            "is_public": True,
            "mature_image_url": "https://example.com/mature-avatar.png",
            "mature_cover_url": "https://example.com/mature-cover.png",
            "mature_video_url": "https://example.com/mature-video.mp4",
        }

        with patch.object(character_service, 'get_character_by_id', new_callable=AsyncMock) as mock_get:
            with patch.object(db, 'execute', new_callable=AsyncMock) as mock_execute:
                mock_get.side_effect = [mock_existing, mock_updated]
                mock_execute.return_value = None

                result = await character_service.update_character(
                    "char_001",
                    CharacterUpdate(
                        mature_image_url="https://example.com/mature-avatar.png",
                        mature_cover_url="https://example.com/mature-cover.png",
                        mature_video_url="https://example.com/mature-video.mp4",
                    ),
                )

                assert result is not None
                sql = mock_execute.call_args[0][0]
                params = mock_execute.call_args[0][1]
                assert "mature_image_url" in sql
                assert "mature_cover_url" in sql
                assert "mature_video_url" in sql
                assert "https://example.com/mature-avatar.png" in params
                assert "https://example.com/mature-cover.png" in params
                assert "https://example.com/mature-video.mp4" in params


class TestCharacterServiceDeleteCharacter:
    
    @pytest.mark.asyncio
    async def test_delete_character_not_found(self):
        from app.services.character_service import character_service
        
        with patch.object(character_service, 'get_character_by_id', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            result = await character_service.delete_character("non_existent")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_character_success(self):
        from app.services.character_service import character_service
        from app.core.database import db
        
        mock_existing = {"id": "char_001", "name": "Test"}
        
        with patch.object(character_service, 'get_character_by_id', new_callable=AsyncMock) as mock_get:
            with patch.object(db, 'execute', new_callable=AsyncMock) as mock_execute:
                mock_get.return_value = mock_existing
                mock_execute.return_value = None
                
                result = await character_service.delete_character("char_001")
                
                assert result is True
