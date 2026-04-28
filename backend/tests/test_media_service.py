import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.media_service import MediaService
from app.services.media import (
    ControlNetConfig,
    ImageGenerationResult,
    IPAdapterConfig,
    NovitaImageProvider,
)


class TestMediaServiceNovita:

    @pytest.fixture
    def mock_settings(self):
        settings = MagicMock()
        settings.novita_api_key = "test-novita-key"
        settings.novita_base_url = "https://api.novita.ai/v3"
        settings.elevenlabs_api_key = "test-elevenlabs-key"
        settings.elevenlabs_base_url = "https://api.elevenlabs.io"
        return settings

    @pytest.fixture
    async def media_service(self, mock_settings):
        async def _mock_get_config_value(key):
            mapping = {
                "NOVITA_API_KEY": mock_settings.novita_api_key,
                "NOVITA_BASE_URL": mock_settings.novita_base_url,
                "ELEVENLABS_API_KEY": mock_settings.elevenlabs_api_key,
                "ELEVENLABS_BASE_URL": mock_settings.elevenlabs_base_url,
            }
            return mapping.get(key)

        with patch("app.services.media_service.get_settings", return_value=mock_settings):
            with patch("app.services.media_service.ConfigService.get_config_value", side_effect=_mock_get_config_value):
                service = MediaService()
                await service.refresh_providers()
                return service

    @pytest.mark.asyncio
    async def test_media_service_init_with_novita_key(self, media_service):
        assert "novita" in media_service._image_providers
        assert isinstance(media_service._image_providers["novita"], NovitaImageProvider)

    @pytest.mark.asyncio
    async def test_get_novita_provider_by_name(self, media_service):
        provider = media_service.get_image_provider("novita")
        assert provider is not None
        assert isinstance(provider, NovitaImageProvider)

    @pytest.mark.asyncio
    async def test_get_default_provider_returns_novita(self, media_service):
        provider = media_service.get_image_provider()
        assert isinstance(provider, NovitaImageProvider)

    @pytest.mark.asyncio
    async def test_media_service_generate_image_with_novita(self, media_service):
        with patch.object(NovitaImageProvider, "generate_image") as mock_generate:
            mock_generate.return_value = ImageGenerationResult(
                image_url="https://novita.ai/test_image.png"
            )

            result = await media_service.generate_image(
                prompt="A test image",
                provider="novita"
            )

            assert result.image_url == "https://novita.ai/test_image.png"
            mock_generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_media_service_no_provider_error(self, mock_settings):
        mock_settings.novita_api_key = None

        with patch("app.services.media_service.get_settings", return_value=mock_settings):
            service = MediaService()

            with pytest.raises(ValueError, match="Image provider nonexistent not available"):
                await service.generate_image(
                    prompt="test",
                    provider="nonexistent"
                )

    @pytest.mark.asyncio
    async def test_media_service_has_only_novita_provider(self, media_service):
        assert len(media_service._image_providers) == 2
        assert "novita" in media_service._image_providers
        assert "z_image_turbo_lora" in media_service._image_providers

    def test_normalize_novita_media_base_url_adds_v3(self):
        assert (
            MediaService._normalize_novita_base_url("https://api.novita.ai")
            == "https://api.novita.ai/v3"
        )

    def test_normalize_novita_media_base_url_fixes_openai_url(self):
        assert (
            MediaService._normalize_novita_base_url("https://api.novita.ai/openai/v1")
            == "https://api.novita.ai/v3"
        )

    @pytest.mark.asyncio
    async def test_img2img_strips_data_url_prefixes_from_nested_images(self, monkeypatch):
        captured = {}

        class FakeResponse:
            is_error = False
            status_code = 200
            text = ""
            request = MagicMock()

            def json(self):
                return {"task_id": "task_123"}

        class FakeAsyncClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return None

            async def post(self, *args, **kwargs):
                captured["payload"] = kwargs["json"]
                return FakeResponse()

        import httpx

        monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

        provider = NovitaImageProvider(api_key="test-key", base_url="https://api.novita.ai/v3")
        provider._download_image_base64 = AsyncMock(
            return_value="data:image/png;base64,aW5pdC1pbWFnZQ=="
        )

        task_id = await provider.img2img_async(
            init_image_url="https://example.com/init.png",
            prompt="test",
            ip_adapters=[
                IPAdapterConfig(
                    image_base64="data:image/png;base64,aXAtYWRhcHRlcg==",
                    strength=0.4,
                )
            ],
            controlnet=ControlNetConfig(
                model_name="controlnet-openpose-sdxl-1.0",
                image_base64="data:image/png;base64,Y29udHJvbG5ldA==",
            ),
        )

        request = captured["payload"]["request"]
        assert task_id == "task_123"
        assert request["image_base64"] == "aW5pdC1pbWFnZQ=="
        assert request["ip_adapters"][0]["image_base64"] == "aXAtYWRhcHRlcg=="
        assert request["controlnet"]["units"][0]["image_base64"] == "Y29udHJvbG5ldA=="
