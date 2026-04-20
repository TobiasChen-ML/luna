import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import hashlib

from app.services.voice_service import VoiceService, TTS_CACHE_PREFIX, TTS_CACHE_TTL


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.get_json = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.set_json = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def mock_httpx_client():
    client = AsyncMock()
    response = MagicMock()
    response.status_code = 200
    response.content = b"fake_audio_data"
    client.post = AsyncMock(return_value=response)
    return client


@pytest.fixture
def voice_service_with_mocks(mock_redis, mock_httpx_client):
    with patch("app.services.voice_service.get_settings") as mock_settings:
        settings = MagicMock()
        settings.elevenlabs_api_key = "test_key"
        settings.elevenlabs_base_url = "https://api.elevenlabs.io/v1"
        mock_settings.return_value = settings
        
        service = VoiceService(redis=mock_redis)
        service.client = mock_httpx_client
        return service


class TestTTSCache:
    
    def test_cache_key_generation(self, voice_service_with_mocks):
        key1 = voice_service_with_mocks._get_tts_cache_key(
            text="Hello world",
            voice_id="voice_001",
            provider="elevenlabs",
            speed=1.0,
        )
        
        key2 = voice_service_with_mocks._get_tts_cache_key(
            text="Hello world",
            voice_id="voice_001",
            provider="elevenlabs",
            speed=1.0,
        )
        
        key3 = voice_service_with_mocks._get_tts_cache_key(
            text="Different text",
            voice_id="voice_001",
            provider="elevenlabs",
            speed=1.0,
        )
        
        assert key1 == key2
        assert key1 != key3
        assert key1.startswith(TTS_CACHE_PREFIX)
    
    def test_cache_key_includes_all_params(self, voice_service_with_mocks):
        key1 = voice_service_with_mocks._get_tts_cache_key(
            text="Hello",
            voice_id="voice_001",
            provider="elevenlabs",
            speed=1.0,
        )
        
        key2 = voice_service_with_mocks._get_tts_cache_key(
            text="Hello",
            voice_id="voice_002",
            provider="elevenlabs",
            speed=1.0,
        )
        
        key3 = voice_service_with_mocks._get_tts_cache_key(
            text="Hello",
            voice_id="voice_001",
            provider="dashscope",
            speed=1.0,
        )
        
        key4 = voice_service_with_mocks._get_tts_cache_key(
            text="Hello",
            voice_id="voice_001",
            provider="elevenlabs",
            speed=1.5,
        )
        
        assert key1 != key2
        assert key1 != key3
        assert key1 != key4
    
    @pytest.mark.asyncio
    async def test_tts_cache_hit(self, voice_service_with_mocks, mock_redis):
        cached_result = {
            "audio_url": "https://storage.example.com/cached_audio.mp3",
            "duration": 5.0,
            "voice_id": "voice_001",
            "provider": "elevenlabs",
        }
        mock_redis.get_json.return_value = cached_result
        
        result = await voice_service_with_mocks.generate_tts(
            text="Hello world",
            voice_id="voice_001",
            provider="elevenlabs",
            use_cache=True,
        )
        
        assert result == cached_result
        mock_redis.get_json.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tts_cache_miss_stores_result(self, voice_service_with_mocks, mock_redis, mock_httpx_client):
        mock_redis.get_json.return_value = None
        
        with patch.object(voice_service_with_mocks, "_store_audio", return_value="https://storage.example.com/audio.mp3"):
            result = await voice_service_with_mocks.generate_tts(
                text="Hello world",
                voice_id="voice_001",
                provider="elevenlabs",
                use_cache=True,
            )
        
        assert result["audio_url"] == "https://storage.example.com/audio.mp3"
        assert result["provider"] == "elevenlabs"
        
        mock_redis.set_json.assert_called()
        call_args = mock_redis.set_json.call_args
        assert call_args.kwargs["ex"] == TTS_CACHE_TTL
    
    @pytest.mark.asyncio
    async def test_tts_skip_cache(self, voice_service_with_mocks, mock_redis, mock_httpx_client):
        with patch.object(voice_service_with_mocks, "_store_audio", return_value="https://storage.example.com/audio.mp3"):
            result = await voice_service_with_mocks.generate_tts(
                text="Hello world",
                voice_id="voice_001",
                provider="elevenlabs",
                use_cache=False,
            )
        
        assert result["audio_url"] == "https://storage.example.com/audio.mp3"
        
        mock_redis.get_json.assert_not_called()
        mock_redis.set_json.assert_not_called()


class TestTextCleaning:
    
    def test_clean_text_removes_brackets(self, voice_service_with_mocks):
        result = voice_service_with_mocks._clean_text_for_tts("Hello [waves] world")
        assert result == "Hello  world"
    
    def test_clean_text_removes_asterisks(self, voice_service_with_mocks):
        result = voice_service_with_mocks._clean_text_for_tts("Hello *smiles* world")
        assert result == "Hello  world"
    
    def test_clean_text_replaces_newlines(self, voice_service_with_mocks):
        result = voice_service_with_mocks._clean_text_for_tts("Hello\nworld\ntest")
        assert result == "Hello world test"
    
    def test_clean_text_strips_whitespace(self, voice_service_with_mocks):
        result = voice_service_with_mocks._clean_text_for_tts("  Hello world  ")
        assert result == "Hello world"


class TestLiveKitToken:
    
    @pytest.mark.asyncio
    async def test_generate_voice_token_without_livekit(self, voice_service_with_mocks, mock_redis):
        with patch("app.services.voice_service.get_settings") as mock_settings:
            settings = MagicMock()
            settings.livekit_api_key = None
            settings.livekit_api_secret = None
            settings.livekit_ws_url = None
            mock_settings.return_value = settings
            
            service = VoiceService(redis=mock_redis)
            
            result = await service.generate_voice_token(
                session_id="session_001",
                user_id="user_001",
                character_id="char_001",
            )
        
        assert "token" in result
        assert "room_name" in result
        assert result["session_id"] == "session_001"
        
        mock_redis.set_json.assert_called()
    
    @pytest.mark.asyncio
    async def test_generate_voice_token_with_room_name(self, voice_service_with_mocks, mock_redis):
        result = await voice_service_with_mocks.generate_voice_token(
            session_id="session_001",
            user_id="user_001",
            character_id="char_001",
            room_name="custom_room_123",
        )
        
        assert result["room_name"] == "custom_room_123"
