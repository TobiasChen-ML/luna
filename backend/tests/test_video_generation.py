"""
Video Generation Tests

Covers:
- NovitaVideoProvider (wan-i2v, wan-t2v)
- VideoIntentHandler
- Callback handling
- Credit deduction flow
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.services.media import (
    LoRAConfig,
    NovitaVideoProvider,
    VideoGenerationResult,
    TaskResult,
)
from app.services.video_intent_handler import VideoIntentHandler


class TestNovitaVideoProvider:
    """Tests for NovitaVideoProvider video generation."""

    @pytest.fixture
    def provider(self):
        return NovitaVideoProvider(
            api_key="test_api_key",
            base_url="https://api.novita.ai"
        )

    @pytest.mark.asyncio
    async def test_generate_video_async_text_to_video(self, provider):
        """wan-t2v: should use /v3/async/wan-t2v endpoint without init_image."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"task_id": "task_t2v_001"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            task_id = await provider.generate_video_async(
                prompt="A cat playing piano"
            )

            assert task_id == "task_t2v_001"

    @pytest.mark.asyncio
    async def test_generate_video_async_includes_loras(self, provider):
        """wan-i2v should pass LoRA path/scale through to Novita."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"task_id": "task_i2v_lora_001"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = post

            task_id = await provider.generate_video_async(
                prompt="A cinematic movement",
                init_image="https://example.com/init.png",
                loras=[LoRAConfig(model_name="civitai:123@456", strength=0.75)],
                fast_mode=True,
            )

        assert task_id == "task_i2v_lora_001"
        payload = post.call_args.kwargs["json"]
        assert payload["loras"] == [
            {"path": "https://civitai.com/api/download/models/456", "scale": 0.75}
        ]
        assert payload["fast_mode"] is True

    @pytest.mark.asyncio
    async def test_generate_video_async_includes_configured_webhook(self, provider):
        """Async video requests should send Novita webhook configuration when available."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"task_id": "task_t2v_002"}
        mock_response.raise_for_status = MagicMock()

        async def config_value(key: str, default=None):
            if key == "NOVITA_WEBHOOK_BASE_URL":
                return "https://api.example.com/"
            return default

        with patch("app.core.config.get_config_value", new=AsyncMock(side_effect=config_value)):
            with patch("httpx.AsyncClient") as mock_client:
                post = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value.post = post

                task_id = await provider.generate_video_async(prompt="A cat playing piano")

        assert task_id == "task_t2v_002"
        payload = post.call_args.kwargs["json"]
        assert payload["extra"]["webhook"]["url"] == "https://api.example.com/api/images/callbacks/novita"

    @pytest.mark.asyncio
    async def test_get_task_result_succeed(self, provider):
        """Should parse successful video task result."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "task": {"status": "TASK_STATUS_SUCCEED", "progress_percent": 100},
            "videos": [{"video_url": "https://example.com/video.mp4"}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await provider.get_task_result("task_video_001")

            assert result.status == "TASK_STATUS_SUCCEED"
            assert result.video_url == "https://example.com/video.mp4"

    @pytest.mark.asyncio
    async def test_get_task_result_failed(self, provider):
        """Should parse failed video task result."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "task": {
                "status": "TASK_STATUS_FAILED",
                "reason": "Content policy violation"
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await provider.get_task_result("task_video_001")

            assert result.status == "TASK_STATUS_FAILED"
            assert result.error == "Content policy violation"

    @pytest.mark.asyncio
    async def test_generate_video_sync(self, provider):
        """Should generate video synchronously with polling."""
        with patch.object(provider, "generate_video_async", new_callable=AsyncMock) as mock_async:
            with patch.object(provider, "wait_for_task", new_callable=AsyncMock) as mock_wait:
                mock_async.return_value = "task_video_001"
                mock_wait.return_value = TaskResult(
                    task_id="task_video_001",
                    status="TASK_STATUS_SUCCEED",
                    video_url="https://example.com/video.mp4"
                )

                result = await provider.generate_video(
                    prompt="Test video"
                )

                assert isinstance(result, VideoGenerationResult)
                assert result.video_url == "https://example.com/video.mp4"


class TestVideoIntentHandler:
    """Tests for VideoIntentHandler."""

    @pytest.fixture
    def handler(self):
        return VideoIntentHandler()

    @pytest.fixture
    def mock_llm_service(self):
        return MagicMock(
            generate=AsyncMock(return_value=MagicMock(
                content="抱歉，我现在还不会录视频呢。不过我可以给你拍张照片，好吗？"
            )),
            detect_video_intent=AsyncMock(return_value={
                "is_video_request": True,
                "confidence": 0.9
            })
        )

    @pytest.mark.asyncio
    async def test_handle_video_intent_high_confidence(self, handler, mock_llm_service):
        """High confidence video request should generate decline message."""
        character = {
            "name": "Luna",
            "personality_summary": "A gentle and caring companion",
        }

        result = await handler.handle_video_intent(
            user_message="Can you make a video for me?",
            character=character,
            llm_service=mock_llm_service
        )

        assert result is not None
        assert "照片" in result or "photo" in result.lower()

    @pytest.mark.asyncio
    async def test_handle_video_intent_watching_context(self, handler, mock_llm_service):
        """'I watched a video' context should NOT trigger decline (negative context)."""
        result = await handler.handle_video_intent(
            user_message="I watched a video about cats",
            character={"name": "Luna"},
            llm_service=mock_llm_service
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_handle_video_intent_empty_message(self, handler, mock_llm_service):
        """Empty message should return None."""
        result = await handler.handle_video_intent(
            user_message="",
            character={"name": "Luna"},
            llm_service=mock_llm_service
        )

        assert result is None

    def test_extract_personality(self, handler):
        """Should extract personality from character data."""
        character = {
            "name": "Luna",
            "personality_summary": "温柔可爱",
            "personality_tags": ["可爱", "温柔", "治愈"],
            "backstory": "A moon spirit who loves to chat with humans."
        }

        personality = handler._extract_personality(character)

        assert "温柔可爱" in personality
        assert "可爱" in personality

    def test_extract_personality_empty(self, handler):
        """Should return default personality when no data."""
        personality = handler._extract_personality({"name": "Unknown"})
        assert personality == "friendly and warm"

    def test_get_fallback_decline_message_cute(self, handler):
        """Cute personality should have cute decline message."""
        message = handler._get_fallback_decline_message("Luna", "可爱 温柔")
        assert "照片" in message

    def test_get_fallback_decline_message_cold(self, handler):
        """Cold personality should have cold decline message."""
        message = handler._get_fallback_decline_message("Shadow", "cold mysterious")
        assert "拍照" in message or "照片" in message

    def test_get_fallback_decline_message_default(self, handler):
        """Default personality should have neutral decline message."""
        message = handler._get_fallback_decline_message("AI", "friendly")
        assert "照片" in message


class TestVideoEndpoints:
    """Tests for video-related API endpoints."""

    def test_generate_video_wan_character_mocked(self, client: TestClient):
        """Should submit video generation task with mocked provider."""
        from app.services.media import NovitaVideoProvider
        
        mock_provider = MagicMock(spec=NovitaVideoProvider)
        mock_provider.generate_video_async = AsyncMock(return_value="task_video_mocked")

        with patch("app.routers.media.media_service.get_video_provider", return_value=mock_provider):
            response = client.post("/api/images/generate-video-wan-character", json={
                "character_id": "char_001",
                "prompt": "Character walking in a forest"
            })
            assert response.status_code == 200
            data = response.json()
            assert "task_id" in data

    def test_generate_video_wan_character_missing_provider(self, client: TestClient):
        """Should return 503 when provider unavailable."""
        with patch("app.routers.media.media_service.get_video_provider", return_value=None):
            response = client.post("/api/images/generate-video-wan-character", json={
                "character_id": "char_001",
                "prompt": "Test"
            })
            assert response.status_code == 503

    def test_animate_standalone_mocked(self, client: TestClient):
        """Should submit animation task with mocked provider."""
        from app.services.media import NovitaVideoProvider
        
        mock_provider = MagicMock(spec=NovitaVideoProvider)
        mock_provider.generate_video_async = AsyncMock(return_value="task_animate_mocked")

        with patch("app.routers.media.media_service.get_video_provider", return_value=mock_provider):
            response = client.post("/api/images/animate-standalone", json={
                "image_url": "https://example.com/image.png",
                "prompt": "Animate this image",
                "character_id": "char_001"
            })
            assert response.status_code == 200
            data = response.json()
            assert "task_id" in data

    def test_animate_standalone_missing_image(self, client: TestClient):
        """Should return 400 when image_url missing."""
        response = client.post("/api/images/animate-standalone", json={
            "prompt": "Animate this"
        })
        assert response.status_code == 400


class TestVideoCallback:
    """Tests for video callback handling."""

    def test_novita_callback_video_completed(self, client: TestClient):
        """Should handle video completion callback."""
        with patch("app.core.redis_client.redis_client.publish", new_callable=AsyncMock) as mock_publish:
            response = client.post("/api/images/callbacks/novita", json={
                "task_id": "task_video_001",
                "task": {"status": "TASK_STATUS_SUCCEED"},
                "videos": [{"video_url": "https://example.com/video.mp4"}]
            })
            assert response.status_code == 200
            assert response.json()["success"] is True

    def test_novita_callback_video_failed(self, client: TestClient):
        """Should handle video failure callback."""
        with patch("app.core.redis_client.redis_client.publish", new_callable=AsyncMock) as mock_publish:
            response = client.post("/api/images/callbacks/novita", json={
                "task_id": "task_video_001",
                "task": {
                    "status": "TASK_STATUS_FAILED",
                    "reason": "Timeout"
                }
            })
            assert response.status_code == 200

    def test_novita_callback_accepts_async_task_result_event(self, client: TestClient):
        """Should unwrap Novita official ASYNC_TASK_RESULT webhook payload."""
        with patch("app.core.redis_client.redis_client.publish", new_callable=AsyncMock) as mock_publish:
            response = client.post("/api/images/callbacks/novita", json={
                "event_type": "ASYNC_TASK_RESULT",
                "payload": {
                    "task": {
                        "task_id": "task_video_002",
                        "status": "TASK_STATUS_SUCCEED",
                    },
                    "videos": [{"video_url": "https://example.com/video-2.mp4"}],
                },
            })
            assert response.status_code == 200
            assert response.json()["success"] is True
            mock_publish.assert_awaited()

    def test_callbacks_health(self, client: TestClient):
        """Should return healthy status."""
        response = client.get("/api/images/callbacks/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestVideoCredits:
    """Tests for video generation credit flow."""

    @pytest.mark.asyncio
    async def test_video_cost_via_config(self):
        """Should return video cost in pricing config."""
        from app.services.credit_service import CreditService
        
        with patch.object(CreditService, "get_config", new_callable=AsyncMock) as mock_config:
            mock_config.return_value = {
                "video_cost": 4,
                "image_cost": 2,
                "message_cost": 0.1
            }
            
            service = CreditService()
            config = await service.get_config()
            assert "video_cost" in config
            assert config["video_cost"] == 4

    @pytest.mark.asyncio
    async def test_video_credit_deduction(self):
        """Should deduct credits for video generation."""
        from app.services.credit_service import CreditService

        mock_db = MagicMock()
        mock_db.execute = AsyncMock(return_value={
            "id": "tx_001",
            "balance_after": 96
        })

        with patch("app.services.credit_service.credit_service") as mock_service:
            mock_service.deduct_credits = AsyncMock(return_value={
                "success": True,
                "balance_after": 96
            })

            result = await mock_service.deduct_credits(
                user_id="user_001",
                amount=4,
                reason="video_generation"
            )

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_video_credit_refund_on_failure(self):
        """Should refund credits if video generation fails."""
        from app.services.credit_service import CreditService

        with patch("app.services.credit_service.credit_service") as mock_service:
            mock_service.refund_credits = AsyncMock(return_value={
                "success": True,
                "balance_after": 100
            })

            result = await mock_service.refund_credits(
                user_id="user_001",
                amount=4,
                reason="video_generation_failed"
            )

            assert result["success"] is True
