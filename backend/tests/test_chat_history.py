import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import logging

from app.services.chat_history_service import ChatHistoryService, REDIS_FAILURE_THRESHOLD


class TestChatHistoryServiceRedisFailure:
    
    @pytest.fixture
    def chat_history_service(self):
        service = ChatHistoryService()
        service._redis_failure_count = 0
        service._redis_degraded = False
        return service
    
    @pytest.fixture
    def mock_redis_failure(self):
        redis_mock = MagicMock()
        redis_mock.get = AsyncMock(side_effect=ConnectionError("Redis connection refused"))
        redis_mock.set = AsyncMock(side_effect=ConnectionError("Redis connection refused"))
        return redis_mock
    
    @pytest.fixture
    def mock_db_messages(self):
        return [
            {"id": "msg_001", "role": "user", "content": "Hello", "created_at": "2026-01-01T00:00:00"},
            {"id": "msg_002", "role": "assistant", "content": "Hi there!", "created_at": "2026-01-01T00:00:01"},
        ]

    def test_redis_failure_counter_increment(self, chat_history_service, mock_redis_failure):
        chat_history_service.redis = mock_redis_failure
        
        initial_count = chat_history_service._redis_failure_count
        chat_history_service._record_redis_failure("test_session", "test_op", Exception("test error"))
        
        assert chat_history_service._redis_failure_count == initial_count + 1
    
    def test_redis_degraded_alert_triggered(self, chat_history_service, mock_redis_failure, caplog):
        chat_history_service.redis = mock_redis_failure
        
        with caplog.at_level(logging.ERROR):
            for i in range(REDIS_FAILURE_THRESHOLD):
                chat_history_service._record_redis_failure(
                    f"session_{i}", f"op_{i}", ConnectionError("Redis down")
                )
        
        assert chat_history_service._redis_degraded is True
        assert any("Redis cache degraded" in record.message for record in caplog.records)
    
    def test_redis_success_resets_degraded_state(self, chat_history_service, mock_redis_failure):
        chat_history_service._redis_failure_count = 5
        chat_history_service._redis_degraded = True
        
        chat_history_service._record_redis_success()
        
        assert chat_history_service._redis_failure_count == 0
        assert chat_history_service._redis_degraded is False
    
    @pytest.mark.asyncio
    async def test_get_cached_messages_fallback_on_redis_failure(self, chat_history_service, mock_redis_failure):
        chat_history_service.redis = mock_redis_failure
        
        result = await chat_history_service._get_cached_messages("test_session")
        
        assert result is None
        assert chat_history_service._redis_failure_count >= 1
    
    @pytest.mark.asyncio
    async def test_cache_message_continues_on_redis_failure(self, chat_history_service, mock_redis_failure):
        chat_history_service.redis = mock_redis_failure
        
        await chat_history_service._cache_message("test_session", "msg_001", "user", "Hello")
        
        assert chat_history_service._redis_failure_count >= 1
    
    @pytest.mark.asyncio
    async def test_redis_health_check_returns_degraded_status(self, chat_history_service, mock_redis_failure):
        chat_history_service.redis = mock_redis_failure
        chat_history_service._redis_degraded = True
        
        result = await chat_history_service.redis_health_check()
        
        assert result["healthy"] is False
        assert result["degraded"] is True
    
    @pytest.mark.asyncio
    async def test_redis_health_check_returns_healthy(self, chat_history_service):
        mock_redis_healthy = MagicMock()
        mock_redis_healthy.get = AsyncMock(return_value=None)
        chat_history_service.redis = mock_redis_healthy
        chat_history_service._redis_degraded = False
        
        result = await chat_history_service.redis_health_check()
        
        assert result["healthy"] is True
        assert result["degraded"] is False


class TestChatHistoryServiceDBFallback:
    
    @pytest.fixture
    def chat_history_service(self):
        service = ChatHistoryService()
        service._redis_failure_count = 0
        service._redis_degraded = False
        return service
    
    @pytest.mark.asyncio
    async def test_get_recent_messages_with_redis_down(self, chat_history_service):
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(side_effect=ConnectionError("Redis down"))
        mock_redis.set = AsyncMock(side_effect=ConnectionError("Redis down"))
        chat_history_service.redis = mock_redis
        
        mock_db_rows = [
            {"id": "msg_001", "role": "user", "content": "Hello", "created_at": "2026-01-01T00:00:00", "image_urls": None, "metadata": None},
            {"id": "msg_002", "role": "assistant", "content": "Hi", "created_at": "2026-01-01T00:00:01", "image_urls": None, "metadata": None},
        ]
        
        with patch.object(chat_history_service, '_get_cached_messages', return_value=None):
            with patch('app.services.chat_history_service.db') as mock_db:
                mock_db.execute = AsyncMock(return_value=mock_db_rows)
                
                messages = await chat_history_service.get_recent_messages("test_session")
                
                assert len(messages) == 2
                assert messages[0]["content"] == "Hello"
                assert messages[1]["content"] == "Hi"
    
    @pytest.mark.asyncio
    async def test_cache_ttl_expiry_triggers_reload(self, chat_history_service):
        mock_redis_expired = MagicMock()
        mock_redis_expired.get = AsyncMock(return_value=None)
        mock_redis_expired.set = AsyncMock(return_value=True)
        chat_history_service.redis = mock_redis_expired
        
        mock_db_rows = [
            {"id": "msg_001", "role": "user", "content": "New message", "created_at": "2026-01-01T00:00:00", "image_urls": None, "metadata": None},
        ]
        
        with patch('app.services.chat_history_service.db') as mock_db:
            mock_db.execute = AsyncMock(return_value=mock_db_rows)
            
            messages = await chat_history_service.get_recent_messages("test_session")
            
            assert len(messages) == 1
            assert messages[0]["content"] == "New message"
            mock_redis_expired.set.assert_called_once()


class TestChatHistoryServiceRecovery:
    
    @pytest.fixture
    def chat_history_service(self):
        service = ChatHistoryService()
        service._redis_failure_count = 0
        service._redis_degraded = False
        return service
    
    @pytest.mark.asyncio
    async def test_redis_recovery_clears_degraded_state(self, chat_history_service, caplog):
        chat_history_service._redis_failure_count = 5
        chat_history_service._redis_degraded = True
        
        mock_redis_recovered = MagicMock()
        mock_redis_recovered.get = AsyncMock(return_value={"messages": [{"id": "msg_001"}]})
        mock_redis_recovered.set = AsyncMock(return_value=True)
        chat_history_service.redis = mock_redis_recovered
        
        with caplog.at_level(logging.INFO):
            await chat_history_service._get_cached_messages("test_session")
        
        assert chat_history_service._redis_degraded is False
        assert chat_history_service._redis_failure_count == 0
        assert any("Redis cache recovered" in record.message for record in caplog.records)
