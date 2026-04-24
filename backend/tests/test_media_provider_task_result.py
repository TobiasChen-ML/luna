import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.services.media import NovitaImageProvider


class TestNovitaImageProviderTaskResult:
    @pytest.fixture
    def provider(self):
        return NovitaImageProvider(
            api_key="test_api_key",
            base_url="https://api.novita.ai/v3",
        )

    @pytest.mark.asyncio
    async def test_get_task_result_parses_top_level_status_and_result_data(self, provider):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "TASK_STATUS_SUCCEED",
            "result": {"data": "https://example.com/image-from-result-data.png"},
            "progress": 100,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            result = await provider.get_task_result("task_001")

        assert result.status == "TASK_STATUS_SUCCEED"
        assert result.image_url == "https://example.com/image-from-result-data.png"
        assert result.progress == 100

    @pytest.mark.asyncio
    async def test_get_task_result_retries_on_transient_disconnect(self, provider):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "task": {"status": "TASK_STATUS_SUCCEED", "progress_percent": 100},
            "images": [{"image_url": "https://example.com/retried.png"}],
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=[
                    httpx.RemoteProtocolError("Server disconnected without sending a response."),
                    mock_response,
                ]
            )
            result = await provider.get_task_result("task_002")

        assert result.status == "TASK_STATUS_SUCCEED"
        assert result.image_url == "https://example.com/retried.png"
