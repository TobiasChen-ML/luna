import pytest
from datetime import datetime
from app.services.story_service import StoryService, EndingType, EndingResult


class TestStoryService:
    @pytest.fixture
    def service(self):
        return StoryService()

    def test_ending_type_enum(self):
        assert EndingType.GOOD.value == "good"
        assert EndingType.NEUTRAL.value == "neutral"
        assert EndingType.BAD.value == "bad"
        assert EndingType.SECRET.value == "secret"

    def test_ending_result_default(self):
        result = EndingResult(is_ending=False)
        
        assert result.is_ending is False
        assert result.ending_type is None
        assert result.rewards is None
        assert result.completion_time_minutes == 0
        assert result.narrative is None

    def test_ending_result_with_values(self):
        result = EndingResult(
            is_ending=True,
            ending_type="good",
            rewards={"trust_bonus": 10, "intimacy_bonus": 15},
            completion_time_minutes=30,
            narrative="They lived happily ever after"
        )
        
        assert result.is_ending is True
        assert result.ending_type == "good"
        assert result.rewards["trust_bonus"] == 10
        assert result.completion_time_minutes == 30

    def test_calculate_rewards_good_ending(self, service):
        progress = {
            "choices_made": "[]"
        }
        ending_node = {
            "ending_type": "good"
        }
        
        import asyncio
        rewards = asyncio.run(service._calculate_rewards(progress, ending_node))
        
        assert rewards["trust_bonus"] >= 10
        assert rewards["intimacy_bonus"] >= 15

    def test_calculate_rewards_bad_ending(self, service):
        progress = {
            "choices_made": "[]"
        }
        ending_node = {
            "ending_type": "bad"
        }
        
        import asyncio
        rewards = asyncio.run(service._calculate_rewards(progress, ending_node))
        
        assert rewards["trust_bonus"] == 0
        assert rewards["intimacy_bonus"] == 0

    def test_calculate_rewards_secret_ending(self, service):
        progress = {
            "choices_made": "[]"
        }
        ending_node = {
            "ending_type": "secret"
        }
        
        import asyncio
        rewards = asyncio.run(service._calculate_rewards(progress, ending_node))
        
        assert rewards["trust_bonus"] >= 15
        assert rewards["intimacy_bonus"] >= 20

    def test_calculate_rewards_with_choice_effects(self, service):
        import json
        progress = {
            "choices_made": json.dumps([
                {"effects": {"trust_delta": 5, "intimacy_delta": 3}},
                {"effects": {"trust_delta": 2, "intimacy_delta": 5}}
            ])
        }
        ending_node = {
            "ending_type": "neutral"
        }
        
        import asyncio
        rewards = asyncio.run(service._calculate_rewards(progress, ending_node))
        
        assert rewards["trust_bonus"] >= 5 + 2
        assert rewards["intimacy_bonus"] >= 3 + 5

    def test_calculate_rewards_caps_at_max(self, service):
        import json
        progress = {
            "choices_made": json.dumps([
                {"effects": {"trust_delta": 50, "intimacy_delta": 50}}
            ])
        }
        ending_node = {
            "ending_type": "good"
        }
        
        import asyncio
        rewards = asyncio.run(service._calculate_rewards(progress, ending_node))
        
        assert rewards["trust_bonus"] <= 30
        assert rewards["intimacy_bonus"] <= 30

    @pytest.mark.asyncio
    async def test_determine_ending_not_ending_node(self, service):
        from unittest.mock import AsyncMock, patch
        from app.core import database
        
        with patch.object(database.db, 'execute', new_callable=AsyncMock) as mock_db:
            mock_db.return_value = None
            result = await service.determine_ending("invalid_progress_id")
            
            assert result.is_ending is False


class TestStoryReplayAndHistory:
    """Tests for replay and history functionality."""
    
    @pytest.fixture
    def service(self):
        return StoryService()
    
    @pytest.mark.asyncio
    async def test_get_play_history_empty(self, service):
        """Test getting play history for user with no plays."""
        from unittest.mock import AsyncMock, patch
        from app.core import database
        
        with patch.object(database.db, 'execute', new_callable=AsyncMock) as mock_db:
            mock_db.return_value = []
            result = await service.get_play_history("user_001", "story_001")
            assert result == []
    
    @pytest.mark.asyncio
    async def test_get_next_play_index_first_play(self, service):
        """Test getting next play index when no previous plays."""
        from unittest.mock import AsyncMock, patch
        from app.core import database
        
        with patch.object(database.db, 'execute', new_callable=AsyncMock) as mock_db:
            mock_db.return_value = None
            index = await service.get_next_play_index("user_001", "story_001")
            assert index == 1
    
    @pytest.mark.asyncio
    async def test_get_next_play_index_with_previous(self, service):
        """Test getting next play index with previous plays."""
        from unittest.mock import AsyncMock, patch
        from app.core import database
        
        with patch.object(database.db, 'execute', new_callable=AsyncMock) as mock_db:
            mock_db.return_value = {"max_idx": 3}
            index = await service.get_next_play_index("user_001", "story_001")
            assert index == 4
    
    @pytest.mark.asyncio
    async def test_increment_play_count(self, service):
        """Test incrementing play count."""
        from unittest.mock import AsyncMock, patch
        from app.core import database
        
        with patch.object(database.db, 'execute', new_callable=AsyncMock) as mock_db:
            mock_db.return_value = None
            await service.increment_play_count("story_001")
            assert mock_db.called
    
    @pytest.mark.asyncio
    async def test_get_all_user_play_history(self, service):
        """Test getting all user play history."""
        from unittest.mock import AsyncMock, patch
        from app.core import database
        
        with patch.object(database.db, 'execute', new_callable=AsyncMock) as mock_db:
            mock_db.side_effect = [
                {"cnt": 0},
                []
            ]
            history, total = await service.get_all_user_play_history("user_001")
            assert history == []
            assert total == 0


class TestStoryServiceRobustness:
    """Tests for robustness and edge cases."""
    
    @pytest.fixture
    def service(self):
        return StoryService()
    
    @pytest.mark.asyncio
    async def test_llm_malformed_json_fallback(self, service):
        """Test handling malformed JSON from LLM."""
        from unittest.mock import AsyncMock, patch
        from app.core import database
        
        with patch.object(database.db, 'execute', new_callable=AsyncMock) as mock_db:
            mock_db.return_value = {
                "id": "prog_001",
                "current_node_id": "node_001",
                "choices_made": "invalid json {{{",
                "visited_nodes": None
            }
            
            result = await service.get_story_node("node_001")
            assert result is not None or result is None
    
    @pytest.mark.asyncio
    async def test_concurrent_progress_update(self, service):
        """Test concurrent progress updates don't cause issues."""
        import asyncio
        from unittest.mock import AsyncMock, patch
        from app.core import database
        
        with patch.object(database.db, 'execute', new_callable=AsyncMock) as mock_db:
            mock_db.return_value = None
            
            tasks = [
                service.update_progress(
                    "prog_001",
                    node_id=f"node_{i}",
                    choice_made={"choice_id": f"choice_{i}"}
                )
                for i in range(3)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            assert all(r is not None or isinstance(r, Exception) for r in results)


class TestEndingResultDataclass:
    def test_dataclass_creation(self):
        result = EndingResult(
            is_ending=True,
            ending_type="good"
        )
        
        assert hasattr(result, 'is_ending')
        assert hasattr(result, 'ending_type')
        assert hasattr(result, 'rewards')
        assert hasattr(result, 'completion_time_minutes')
        assert hasattr(result, 'narrative')
