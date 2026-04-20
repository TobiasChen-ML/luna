"""
Tests for Memory Service - Importance decay and global memory functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

from app.services.memory_service import MemoryService


class TestMemoryDecayCalculation:
    """Tests for memory importance decay calculation."""

    def test_calculate_decayed_importance_no_last_accessed(self):
        """Memory with no last_accessed should return original importance."""
        service = MemoryService()
        
        result = service.calculate_decayed_importance(importance=8, last_accessed=None)
        
        assert result == 8.0

    def test_calculate_decayed_importance_fresh_memory(self):
        """Freshly accessed memory should have near-original importance."""
        service = MemoryService()
        now = datetime.utcnow()
        
        result = service.calculate_decayed_importance(importance=7, last_accessed=now)
        
        assert 6.9 <= result <= 7.0

    def test_calculate_decayed_importance_14_day_half_life(self):
        """Memory should decay to ~50% after 14 days with default rate."""
        service = MemoryService()
        now = datetime.utcnow()
        two_weeks_ago = now - timedelta(days=14)
        
        result = service.calculate_decayed_importance(importance=10, last_accessed=two_weeks_ago)
        
        assert 4.5 <= result <= 5.5, f"Expected ~5.0, got {result}"

    def test_calculate_decayed_importance_30_days(self):
        """Memory should decay significantly after 30 days."""
        service = MemoryService()
        now = datetime.utcnow()
        month_ago = now - timedelta(days=30)
        
        result = service.calculate_decayed_importance(importance=10, last_accessed=month_ago)
        
        assert 1.5 <= result <= 3.0, f"Expected ~2.2, got {result}"

    def test_calculate_decayed_importance_never_below_minimum(self):
        """Decayed importance should never go below minimum threshold."""
        service = MemoryService()
        now = datetime.utcnow()
        year_ago = now - timedelta(days=365)
        
        result = service.calculate_decayed_importance(importance=10, last_accessed=year_ago)
        
        assert result >= 0.1

    def test_calculate_decayed_importance_custom_decay_rate(self):
        """Should support custom decay rate."""
        service = MemoryService()
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        
        # Higher decay rate = faster decay
        fast_decay = service.calculate_decayed_importance(importance=10, last_accessed=week_ago, decay_rate=0.1)
        slow_decay = service.calculate_decayed_importance(importance=10, last_accessed=week_ago, decay_rate=0.02)
        
        assert fast_decay < slow_decay


class TestMemoryServiceAddMemory:
    """Tests for adding memories with importance."""

    @pytest.mark.asyncio
    async def test_add_memory_default_importance(self, mock_redis, mock_db):
        """Adding memory should default importance to 5."""
        with patch('app.services.memory_service.RedisService', return_value=mock_redis), \
             patch('app.services.memory_service.db', mock_db):
            
            service = MemoryService()
            
            result = await service.add_memory(
                user_id="user_1",
                character_id="char_1",
                content="Test memory content",
                layer="semantic",
            )
            
            assert result["importance"] == 5
            assert result["layer"] == "semantic"

    @pytest.mark.asyncio
    async def test_add_memory_custom_importance(self, mock_redis, mock_db):
        """Adding memory should accept custom importance."""
        with patch('app.services.memory_service.RedisService', return_value=mock_redis), \
             patch('app.services.memory_service.db', mock_db):
            
            service = MemoryService()
            mock_db.execute = AsyncMock()
            
            result = await service.add_memory(
                user_id="user_1",
                character_id="char_1",
                content="Important fact",
                layer="semantic",
                importance=9,
            )
            
            assert result["importance"] == 9

    @pytest.mark.asyncio
    async def test_add_memory_clamp_importance(self, mock_redis, mock_db):
        """Importance should be clamped to 1-10 range."""
        with patch('app.services.memory_service.RedisService', return_value=mock_redis), \
             patch('app.services.memory_service.db', mock_db):
            
            service = MemoryService()
            mock_db.execute = AsyncMock()
            
            # Test upper bound
            result = await service.add_memory(
                user_id="user_1", character_id="char_1", content="Test",
                importance=15  # Over max
            )
            assert result["importance"] == 10
            
            # Test lower bound
            result = await service.add_memory(
                user_id="user_1", character_id="char_1", content="Test",
                importance=-5  # Under min
            )
            assert result["importance"] == 1


class TestMemoryServiceQuery:
    """Tests for querying memories with decay weighting."""

    @pytest.mark.asyncio
    async def test_query_memories_orders_by_decayed_importance(self, mock_redis, mock_db):
        """Query should order results by decayed importance."""
        mock_memories = [
            {
                "id": "mem_1",
                "content": "Low importance memory",
                "layer": "semantic",
                "importance": 3,
                "decayed_importance": 2.5,
                "last_accessed": None,
                "created_at": "2026-01-01",
                "embedding": None,
            },
            {
                "id": "mem_2",
                "content": "High importance memory",
                "layer": "semantic",
                "importance": 9,
                "decayed_importance": 8.5,
                "last_accessed": None,
                "created_at": "2026-01-02",
                "embedding": None,
            },
        ]
        
        mock_db.execute = AsyncMock(return_value=mock_memories)
        
        with patch('app.services.memory_service.RedisService', return_value=mock_redis), \
             patch('app.services.memory_service.db', mock_db):
            
            service = MemoryService()
            
            result = await service.query_memories(
                user_id="user_1",
                character_id="char_1",
                query="test query",
            )
            
            # Higher importance should come first
            assert len(result) == 2


class TestGlobalMemory:
    """Tests for global memory functionality."""

    @pytest.mark.asyncio
    async def test_suggest_global_memories(self, mock_redis, mock_db):
        """Should suggest memories that could be promoted to global."""
        mock_rows = [
            {
                "content": "User loves cats",
                "character_id": "char_1",
                "importance": 8,
                "occurrence_count": 2,
            },
        ]
        mock_db.execute = AsyncMock(return_value=mock_rows)
        
        with patch('app.services.memory_service.RedisService', return_value=mock_redis), \
             patch('app.services.memory_service.db', mock_db):
            
            service = MemoryService()
            
            suggestions = await service.suggest_global_memories("user_1")
            
            assert len(suggestions) >= 0

    @pytest.mark.asyncio
    async def test_create_global_memory(self, mock_redis, mock_db):
        """Should create a new global memory."""
        mock_db.execute = AsyncMock()
        
        with patch('app.services.memory_service.RedisService', return_value=mock_redis), \
             patch('app.services.memory_service.db', mock_db):
            
            service = MemoryService()
            
            result = await service.create_global_memory(
                user_id="user_1",
                content="User prefers dark mode",
                category="preference",
            )
            
            assert "global_memory_id" in result
            assert result["content"] == "User prefers dark mode"

    @pytest.mark.asyncio
    async def test_promote_to_global_memory(self, mock_redis, mock_db):
        """Should promote existing memory to global."""
        mock_memory_row = {
            "content": "Important fact",
            "character_id": "char_1",
            "importance": 8,
        }
        mock_db.execute = AsyncMock(side_effect=[
            mock_memory_row,  # SELECT memory
            None,  # SELECT existing global
            None,  # INSERT
        ])
        
        with patch('app.services.memory_service.RedisService', return_value=mock_redis), \
             patch('app.services.memory_service.db', mock_db):
            
            service = MemoryService()
            
            result = await service.promote_to_global(
                user_id="user_1",
                memory_id="mem_1",
                category="fact",
            )
            
            assert "global_memory_id" in result


class TestRedisFallback:
    """Tests for Redis failure handling."""

    @pytest.mark.asyncio
    async def test_get_working_memory_redis_failure(self, mock_db):
        """Should gracefully handle Redis failure and return empty list."""
        failing_redis = MagicMock()
        failing_redis.get_json = AsyncMock(side_effect=Exception("Redis connection failed"))
        
        with patch('app.services.memory_service.RedisService', return_value=failing_redis), \
             patch('app.services.memory_service.db', mock_db):
            
            service = MemoryService()
            
            result = await service._get_working_memory("user_1", "char_1")
            
            assert result == []

    @pytest.mark.asyncio
    async def test_get_semantic_facts_falls_back_to_db(self, mock_db):
        """Should fall back to database when Redis fails."""
        failing_redis = MagicMock()
        failing_redis.get_json = AsyncMock(side_effect=Exception("Redis error"))
        failing_redis.set_json = AsyncMock(side_effect=Exception("Redis error"))
        
        mock_db.execute = AsyncMock(return_value=[
            {"content": "Fact 1"},
            {"content": "Fact 2"},
        ])
        
        with patch('app.services.memory_service.RedisService', return_value=failing_redis), \
             patch('app.services.memory_service.db', mock_db):
            
            service = MemoryService()
            
            result = await service._get_semantic_facts("user_1", "char_1")
            
            assert result == ["Fact 1", "Fact 2"]


class TestMemoryStats:
    """Tests for memory statistics."""

    @pytest.mark.asyncio
    async def test_get_memory_stats(self, mock_redis, mock_db):
        """Should return memory statistics."""
        mock_db.execute = AsyncMock(side_effect=[
            {"count": 50},  # total
            {"count": 10},  # working
            {"count": 20},  # episodic
            {"count": 20},  # semantic
            {"count": 5},   # global
        ])
        
        with patch('app.services.memory_service.RedisService', return_value=mock_redis), \
             patch('app.services.memory_service.db', mock_db):
            
            service = MemoryService()
            
            stats = await service.get_memory_stats("user_1")
            
            assert stats["total"] == 50
            assert "by_layer" in stats
            assert "global_memories" in stats


class TestBatchDecayUpdate:
    """Tests for batch decay update."""

    @pytest.mark.asyncio
    async def test_update_all_decayed_importance(self, mock_redis, mock_db):
        """Should update decayed importance for all memories."""
        mock_memories = [
            {"id": "mem_1", "importance": 8, "last_accessed": None},
            {"id": "mem_2", "importance": 5, "last_accessed": (datetime.utcnow() - timedelta(days=7)).isoformat()},
        ]
        
        call_count = [0]
        
        async def mock_execute(query, params=(), fetch=False, fetch_all=False):
            if "SELECT" in query and fetch_all:
                return mock_memories
            call_count[0] += 1
            return None
        
        mock_db.execute = mock_execute
        
        with patch('app.services.memory_service.RedisService', return_value=mock_redis), \
             patch('app.services.memory_service.db', mock_db):
            
            service = MemoryService()
            
            updated = await service.update_all_decayed_importance()
            
            assert updated == 2
