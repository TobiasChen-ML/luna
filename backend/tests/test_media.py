import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from app.services.media import ImageGenerationResult, TaskResult


class TestMediaRouter:
    
    def test_generate_image_async(self, client: TestClient):
        response = client.post("/api/images/generate-async", json={
            "prompt": "A beautiful sunset",
            "width": 512,
            "height": 512
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "status" in data
    
    def test_generate_image(self, client: TestClient):
        response = client.post("/api/images/generate", json={
            "prompt": "A beautiful sunset"
        })
        assert response.status_code == 200
        data = response.json()
        assert "image_url" in data
    
    def test_generate_batch(self, client: TestClient):
        from app.services.media import NovitaImageProvider

        mock_provider = MagicMock(spec=NovitaImageProvider)
        mock_provider.txt2img_async = AsyncMock(side_effect=["task_batch_1", "task_batch_2"])

        with patch("app.routers.media.media_service.get_image_provider", return_value=mock_provider):
            response = client.post("/api/images/generate-batch", json={
                "prompts": ["Sunset", "Sunrise"],
                "width": 512,
                "height": 512
            })

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["id"] == "task_batch_1"
        assert "result" in data
        assert data["result"]["task_ids"] == ["task_batch_1", "task_batch_2"]
    
    def test_suggestion_previews(self, client: TestClient):
        response = client.post("/api/images/suggestion-previews", json={
            "character_id": "char_001",
            "count": 4
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_generate_preset(self, client: TestClient):
        response = client.post("/api/images/generate-preset", json={
            "preset": "fantasy"
        })
        assert response.status_code == 200
        data = response.json()
        assert "image_url" in data
    
    def test_get_preset_characters(self, client: TestClient):
        response = client.get("/api/images/preset-characters")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_preset_by_character(self, client: TestClient):
        response = client.get("/api/images/generate-preset/CharacterName")
        assert response.status_code == 200
        data = response.json()
        assert "character_name" in data
    
    def test_generate_and_save(self, client: TestClient):
        response = client.post("/api/images/generate-and-save", json={
            "prompt": "Test image"
        })
        assert response.status_code == 200
        data = response.json()
        assert "image_url" in data
    
    def test_generate_preset_and_save(self, client: TestClient):
        response = client.post("/api/images/generate-preset-and-save", json={
            "preset": "fantasy"
        })
        assert response.status_code == 200
        data = response.json()
        assert "image_url" in data
    
    def test_animate_direct(self, client: TestClient):
        response = client.post("/api/images/animate-direct", json={
            "image_url": "https://example.com/image.png"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_animate_message(self, client: TestClient):
        response = client.post("/api/images/messages/msg_001/animate", json={
            "style": "default"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_generate_with_character(self, client: TestClient):
        response = client.post("/api/images/generate-with-character/char_001", json={
            "prompt": "Character in a forest"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_animate_standalone(self, client: TestClient):
        from app.services.media import NovitaVideoProvider
        
        mock_provider = MagicMock(spec=NovitaVideoProvider)
        mock_provider.generate_video_async = AsyncMock(return_value="task_animate_mocked")
        
        with patch("app.routers.media.media_service.get_video_provider", return_value=mock_provider):
            response = client.post("/api/images/animate-standalone", json={
                "image_url": "https://example.com/image.png"
            })
            assert response.status_code == 200
            data = response.json()
            assert "task_id" in data
    
    def test_get_task(self, client: TestClient, mock_task_id: str):
        response = client.get(f"/api/images/tasks/{mock_task_id}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data

    def test_get_task_status_maps_to_frontend_shape(self, client: TestClient):
        from app.services.media import NovitaImageProvider

        mock_provider = MagicMock(spec=NovitaImageProvider)
        mock_provider.get_task_result = AsyncMock(
            return_value=TaskResult(
                task_id="task_ok_001",
                status="TASK_STATUS_SUCCEED",
                progress=100.0,
                image_url="https://example.com/result.png",
            )
        )

        with patch("app.routers.media.media_service.get_image_provider", return_value=mock_provider):
            response = client.get("/api/images/tasks/task_ok_001")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "succeeded"
        assert data["raw_status"] == "TASK_STATUS_SUCCEED"
        assert data["result"]["data"] == "https://example.com/result.png"

    def test_get_task_status_transient_provider_disconnect_returns_processing(self, client: TestClient):
        from app.services.media import NovitaImageProvider

        mock_provider = MagicMock(spec=NovitaImageProvider)
        mock_provider.get_task_result = AsyncMock(
            side_effect=httpx.RemoteProtocolError("Server disconnected without sending a response.")
        )

        with patch("app.routers.media.media_service.get_image_provider", return_value=mock_provider):
            response = client.get("/api/images/tasks/task_retry_001")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert data["raw_status"] == "TRANSIENT_NETWORK_ERROR"

    def test_generate_mature_lora_prefers_img2img_when_character_image_exists(self, client: TestClient):
        from app.services.media import NovitaImageProvider

        mock_provider = MagicMock(spec=NovitaImageProvider)
        mock_provider.img2img_async = AsyncMock(return_value="task_img2img_001")
        mock_provider.txt2img_async = AsyncMock(return_value="task_txt2img_001")

        with patch("app.routers.media.media_service.get_image_provider", return_value=mock_provider):
            with patch(
                "app.routers.media.character_service.get_character_by_id",
                AsyncMock(return_value={"id": "char_1", "avatar_url": "https://example.com/base.png"}),
            ):
                response = client.post(
                    "/api/images/generate-mature-lora",
                    json={"prompt": "test prompt", "character_id": "char_1"},
                )

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task_img2img_001"
        mock_provider.img2img_async.assert_awaited_once()
        mock_provider.txt2img_async.assert_not_awaited()

    def test_generate_mature_lora_fallbacks_to_txt2img_when_img2img_submit_fails(self, client: TestClient):
        from app.services.media import NovitaImageProvider

        mock_provider = MagicMock(spec=NovitaImageProvider)
        mock_provider.img2img_async = AsyncMock(side_effect=Exception("img2img submit failed"))
        mock_provider.txt2img_async = AsyncMock(return_value="task_txt2img_002")

        with patch("app.routers.media.media_service.get_image_provider", return_value=mock_provider):
            with patch(
                "app.routers.media.character_service.get_character_by_id",
                AsyncMock(return_value={"id": "char_2", "avatar_url": "https://example.com/base2.png"}),
            ):
                response = client.post(
                    "/api/images/generate-mature-lora",
                    json={"prompt": "test prompt", "character_id": "char_2"},
                )

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task_txt2img_002"
        mock_provider.img2img_async.assert_awaited_once()
        mock_provider.txt2img_async.assert_awaited_once()

    def test_generate_pose_mature_uses_openpose_controlnet(self, client: TestClient):
        from app.services.media import NovitaImageProvider

        mock_provider = MagicMock(spec=NovitaImageProvider)
        mock_provider._download_image_base64 = AsyncMock(return_value="base64-image")
        mock_provider.img2img_async = AsyncMock(return_value="task_pose_001")

        with patch("app.routers.media.media_service.get_image_provider", return_value=mock_provider):
            with patch(
                "app.routers.media.character_service.get_character_by_id",
                AsyncMock(return_value={"id": "char_3", "avatar_url": "https://example.com/avatar.png"}),
            ):
                response = client.post(
                    "/api/images/generate-pose-mature",
                    json={
                        "prompt": "test prompt",
                        "character_id": "char_3",
                        "pose_image_url": "https://example.com/pose.png",
                    },
                )

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task_pose_001"
        controlnet = mock_provider.img2img_async.await_args.kwargs["controlnet"]
        assert controlnet.model_name == "controlnet-openpose-sdxl-1.0"
        assert controlnet.preprocessor == "dwpose"
        assert controlnet.strength == 1.0
        assert controlnet.guidance_end == 1.0
        assert mock_provider.img2img_async.await_args.kwargs["strength"] == 0.75
        ip_adapters = mock_provider.img2img_async.await_args.kwargs["ip_adapters"]
        assert ip_adapters[0].strength == 0.25
    
    def test_generate_video_wan(self, client: TestClient):
        response = client.post("/api/images/generate-video-wan-character", json={
            "character_id": "char_001",
            "prompt": "Character walking"
        })
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
    
    def test_save_media(self, client: TestClient):
        response = client.post("/api/images/save-media", json={
            "url": "https://example.com/image.png",
            "type": "image"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_my_media(self, client: TestClient):
        response = client.get("/api/images/my-media")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_generate_voice_token(self, client: TestClient):
        response = client.post("/api/images/voice/generate_token")
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
    
    def test_generate_message_audio(self, client: TestClient):
        response = client.post("/api/images/voice/messages/msg_001/audio", json={
            "text": "Hello world"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_request_voice_note(self, client: TestClient):
        response = client.post("/api/images/voice/request-note", json={
            "character_id": "char_001",
            "text": "Voice note text"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_novita_callback(self, client: TestClient):
        response = client.post("/api/images/callbacks/novita", json={
            "task_id": "task_001",
            "status": "completed"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_media_callback(self, client: TestClient):
        response = client.post("/api/images/callbacks/media", json={
            "task_id": "task_001"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_callbacks_health(self, client: TestClient):
        response = client.get("/api/images/callbacks/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
