import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.media_service import MediaService
from app.services.media import NovitaImageProvider, ImageGenerationResult


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
    def media_service(self, mock_settings):
        with patch("app.services.media_service.get_settings", return_value=mock_settings):
            service = MediaService()
            return service

    def test_media_service_init_with_novita_key(self, media_service):
        assert "novita" in media_service._image_providers
        assert isinstance(media_service._image_providers["novita"], NovitaImageProvider)

    def test_get_novita_provider_by_name(self, media_service):
        provider = media_service.get_image_provider("novita")
        assert provider is not None
        assert isinstance(provider, NovitaImageProvider)

    def test_get_default_provider_returns_novita(self, media_service):
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

    def test_media_service_has_only_novita_provider(self, media_service):
        assert len(media_service._image_providers) == 1
        assert "novita" in media_service._image_providers
