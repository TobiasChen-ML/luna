import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.voice_call_service import VoiceCallService, voice_call_service
from app.services.credit_service import InsufficientCreditsError


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.get_json = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.set_json = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def mock_credit_service():
    service = AsyncMock()
    service.get_config = AsyncMock(return_value={
        "voice_call_per_minute": 3,
        "message_cost": 0.1,
        "voice_cost": 0.2,
        "image_cost": 2,
        "video_cost": 4,
    })
    service.get_balance = AsyncMock(return_value={"total": 100.0})
    service.deduct_credits = AsyncMock(return_value=True)
    return service


@pytest.fixture
def voice_call_service_with_mocks(mock_redis, mock_credit_service):
    service = VoiceCallService(
        redis=mock_redis,
        credit_service=mock_credit_service,
    )
    return service


class TestVoiceCallService:
    
    @pytest.mark.asyncio
    async def test_start_call(self, voice_call_service_with_mocks, mock_redis):
        result = await voice_call_service_with_mocks.start_call(
            room_name="test_room_123",
            user_id="user_001",
            character_id="char_001",
            session_id="session_001",
        )
        
        assert result["room_name"] == "test_room_123"
        assert result["user_id"] == "user_001"
        assert result["character_id"] == "char_001"
        assert result["status"] == "active"
        assert result["start_time"] is not None
        assert result["duration_seconds"] == 0
        
        mock_redis.set_json.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_call(self, voice_call_service_with_mocks, mock_redis):
        mock_redis.get_json.return_value = {
            "room_name": "test_room",
            "user_id": "user_001",
            "status": "active",
        }
        
        result = await voice_call_service_with_mocks.get_call("test_room")
        
        assert result is not None
        assert result["room_name"] == "test_room"
        mock_redis.get_json.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_call_not_found(self, voice_call_service_with_mocks, mock_redis):
        mock_redis.get_json.return_value = None
        
        result = await voice_call_service_with_mocks.get_call("nonexistent_room")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_end_call(self, voice_call_service_with_mocks, mock_redis, mock_credit_service):
        call_data = {
            "room_name": "test_room",
            "user_id": "user_001",
            "character_id": "char_001",
            "session_id": "session_001",
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None,
            "duration_seconds": 0,
            "credits_charged": 0,
            "status": "active",
        }
        mock_redis.get_json.return_value = call_data
        
        result = await voice_call_service_with_mocks.end_call("test_room")
        
        assert result is not None
        assert result["status"] == "ended"
        assert result["duration_seconds"] >= 0
        assert result["end_time"] is not None
    
    @pytest.mark.asyncio
    async def test_end_call_already_ended(self, voice_call_service_with_mocks, mock_redis):
        call_data = {
            "room_name": "test_room",
            "user_id": "user_001",
            "status": "ended",
            "duration_seconds": 60,
            "credits_charged": 3.0,
        }
        mock_redis.get_json.return_value = call_data
        
        result = await voice_call_service_with_mocks.end_call("test_room")
        
        assert result["status"] == "ended"
        assert result["credits_charged"] == 3.0
    
    @pytest.mark.asyncio
    async def test_end_call_not_found(self, voice_call_service_with_mocks, mock_redis):
        mock_redis.get_json.return_value = None
        
        result = await voice_call_service_with_mocks.end_call("nonexistent_room")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_check_credits_for_call_sufficient(self, voice_call_service_with_mocks, mock_credit_service):
        mock_credit_service.get_balance.return_value = {"total": 10.0}
        
        result = await voice_call_service_with_mocks.check_credits_for_call(
            user_id="user_001",
            estimated_minutes=1.0,
        )
        
        assert result["has_sufficient_credits"] is True
        assert result["credits_per_minute"] == 3
        assert result["required_credits"] == 3.0
    
    @pytest.mark.asyncio
    async def test_check_credits_for_call_insufficient(self, voice_call_service_with_mocks, mock_credit_service):
        mock_credit_service.get_balance.return_value = {"total": 1.0}
        
        result = await voice_call_service_with_mocks.check_credits_for_call(
            user_id="user_001",
            estimated_minutes=5.0,
        )
        
        assert result["has_sufficient_credits"] is False
        assert result["required_credits"] == 15.0
    
    @pytest.mark.asyncio
    async def test_get_active_call_duration(self, voice_call_service_with_mocks, mock_redis):
        import time
        
        start_time = datetime.utcnow()
        call_data = {
            "room_name": "test_room",
            "user_id": "user_001",
            "status": "active",
            "start_time": start_time.isoformat(),
        }
        mock_redis.get_json.return_value = call_data
        
        result = await voice_call_service_with_mocks.get_active_call_duration("test_room")
        
        assert result >= 0
    
    @pytest.mark.asyncio
    async def test_get_active_call_duration_inactive(self, voice_call_service_with_mocks, mock_redis):
        call_data = {
            "room_name": "test_room",
            "user_id": "user_001",
            "status": "ended",
            "start_time": datetime.utcnow().isoformat(),
        }
        mock_redis.get_json.return_value = call_data
        
        result = await voice_call_service_with_mocks.get_active_call_duration("test_room")
        
        assert result == 0.0


class TestVoiceCallBilling:
    
    @pytest.mark.asyncio
    async def test_billing_calculation_1_minute(self, voice_call_service_with_mocks, mock_credit_service, mock_redis):
        import time
        
        start_time = datetime.utcnow()
        call_data = {
            "room_name": "test_room",
            "user_id": "user_001",
            "character_id": "char_001",
            "session_id": "session_001",
            "start_time": start_time.isoformat(),
            "status": "active",
        }
        mock_redis.get_json.return_value = call_data
        
        result = await voice_call_service_with_mocks.end_call("test_room")
        
        assert result["credits_charged"] >= 0
        
        if mock_credit_service.deduct_credits.called:
            call_args = mock_credit_service.deduct_credits.call_args
            assert call_args.kwargs["usage_type"] == "voice_call"
    
    @pytest.mark.asyncio
    async def test_billing_insufficient_credits(self, voice_call_service_with_mocks, mock_credit_service, mock_redis):
        call_data = {
            "room_name": "test_room",
            "user_id": "user_001",
            "character_id": "char_001",
            "session_id": "session_001",
            "start_time": datetime.utcnow().isoformat(),
            "status": "active",
        }
        mock_redis.get_json.return_value = call_data
        mock_credit_service.get_balance.return_value = {"total": 0.0}
        
        result = await voice_call_service_with_mocks.end_call("test_room")
        
        assert result["status"] == "ended"
        assert result["credits_charged"] == 0.0
