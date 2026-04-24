from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.services.media import NovitaImageProvider, NovitaVideoProvider


def _clear_guest_state() -> None:
    from app.routers import chat as chat_router

    chat_router._guest_states.clear()


def test_real_chat_stream_uses_admin_message_cost(client: TestClient):
    with patch(
        "app.routers.chat._resolve_authenticated_user_id",
        return_value="user_real_001",
    ), patch(
        "app.routers.chat.chat_history_service.get_or_create_session",
        AsyncMock(return_value={"id": "sess_001", "script_id": None}),
    ), patch(
        "app.routers.chat._assign_or_rotate_bound_script",
        AsyncMock(return_value=(None, None, False)),
    ), patch(
        "app.routers.chat.content_safety.check_input",
        AsyncMock(return_value=SimpleNamespace(is_safe=True)),
    ), patch(
        "app.routers.chat.DatabaseService.get_user_by_id",
        AsyncMock(return_value=SimpleNamespace(id="user_real_001", tier="free")),
    ), patch(
        "app.routers.chat.credit_service.get_config",
        AsyncMock(return_value={"message_cost": 1.5, "voice_cost": 0.2, "image_cost": 3, "video_cost": 4}),
    ), patch(
        "app.routers.chat.credit_service.get_balance",
        AsyncMock(return_value={"total": 10.0}),
    ), patch(
        "app.routers.chat.credit_service.deduct_credits",
        AsyncMock(return_value=True),
    ) as mock_deduct, patch(
        "app.routers.chat.character_service.get_character_by_id",
        AsyncMock(return_value={"id": "char_001", "name": "Roxy", "voice_id": None}),
    ), patch(
        "app.routers.chat.video_intent_handler.handle_video_intent",
        AsyncMock(return_value="video declined"),
    ):
        response = client.post(
            "/api/chat/stream",
            json={"character_id": "char_001", "message": "hello"},
        )

    assert response.status_code == 200
    mock_deduct.assert_awaited_once_with(
        user_id="user_real_001",
        amount=1.5,
        usage_type="message",
        character_id="char_001",
        session_id="sess_001",
    )


def test_guest_chat_send_deducts_message_cost_from_admin_config(client: TestClient):
    _clear_guest_state()
    with patch(
        "app.routers.chat.credit_service.get_config",
        AsyncMock(return_value={"message_cost": 2.0, "voice_cost": 0.2, "image_cost": 3, "video_cost": 4}),
    ):
        response = client.post(
            "/api/chat/guest/send",
            json={"character_id": "char_001", "message": "hello guest"},
        )
    assert response.status_code == 200
    assert response.json()["credits_remaining"] == 18.0


def test_guest_audio_generate_returns_audio_and_deducts_voice_cost(client: TestClient):
    _clear_guest_state()
    with patch(
        "app.routers.chat.credit_service.get_config",
        AsyncMock(return_value={"message_cost": 0.1, "voice_cost": 3.0, "image_cost": 3, "video_cost": 4}),
    ), patch(
        "app.routers.chat.character_service.get_character_by_id",
        AsyncMock(return_value={"id": "char_001", "voice_id": "voice_001"}),
    ), patch(
        "app.routers.chat.VoiceService.generate_tts",
        AsyncMock(return_value={"audio_url": "https://example.com/audio.mp3", "duration": 1.8}),
    ):
        response = client.post(
            "/api/chat/guest/audio/generate",
            json={"character_id": "char_001", "text": "speak this"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["audio_url"] == "https://example.com/audio.mp3"
    assert data["credits_remaining"] == 17.0


def test_guest_image_generation_deducts_guest_credits(client: TestClient):
    _clear_guest_state()
    mock_provider = NovitaImageProvider(api_key="test-key", base_url="https://example.com")
    mock_provider.generate_with_ip_adapter = AsyncMock(return_value="task_img_guest_001")

    with patch(
        "app.routers.media.credit_service.get_config",
        AsyncMock(return_value={"message_cost": 0.1, "voice_cost": 0.2, "image_cost": 3.0, "video_cost": 4.0}),
    ), patch(
        "app.routers.media.media_service.get_image_provider",
        return_value=mock_provider,
    ):
        response = client.post(
            "/api/images/generate-with-face",
            json={
                "prompt": "test image",
                "face_image_url": "https://example.com/face.png",
                "character_id": "char_001",
            },
        )
    assert response.status_code == 200
    credits = client.get("/api/chat/guest/credits").json()["credits"]
    assert credits == 17.0


def test_guest_video_generation_deducts_guest_credits(client: TestClient):
    _clear_guest_state()
    mock_provider = NovitaVideoProvider(api_key="test-key", base_url="https://example.com")
    mock_provider.generate_video_async = AsyncMock(return_value="task_video_guest_001")

    with patch(
        "app.routers.media.credit_service.get_config",
        AsyncMock(return_value={"message_cost": 0.1, "voice_cost": 0.2, "image_cost": 3.0, "video_cost": 4.0}),
    ), patch(
        "app.routers.media.media_service.get_video_provider",
        return_value=mock_provider,
    ), patch(
        "app.routers.media._resolve_lora_preset",
        AsyncMock(return_value=([], {})),
    ):
        response = client.post(
            "/api/images/generate-video-wan-character",
            json={
                "prompt": "test video",
                "image_url": "https://example.com/base.png",
                "character_id": "char_001",
            },
        )
    assert response.status_code == 200
    credits = client.get("/api/chat/guest/credits").json()["credits"]
    assert credits == 16.0


def test_real_media_image_video_voice_all_deduct(client: TestClient):
    mock_image_provider = NovitaImageProvider(api_key="test-key", base_url="https://example.com")
    mock_image_provider.generate_with_ip_adapter = AsyncMock(return_value="task_img_real_001")
    mock_video_provider = NovitaVideoProvider(api_key="test-key", base_url="https://example.com")
    mock_video_provider.generate_video_async = AsyncMock(return_value="task_video_real_001")

    with patch(
        "app.routers.media._resolve_authenticated_user_id",
        return_value="user_real_002",
    ), patch(
        "app.routers.media.deduct_credits_for_usage",
        AsyncMock(return_value=1.0),
    ) as mock_deduct, patch(
        "app.routers.media.media_service.get_image_provider",
        return_value=mock_image_provider,
    ), patch(
        "app.routers.media.media_service.get_video_provider",
        return_value=mock_video_provider,
    ), patch(
        "app.routers.media._resolve_lora_preset",
        AsyncMock(return_value=([], {})),
    ):
        image_resp = client.post(
            "/api/images/generate-with-face",
            json={"prompt": "p", "face_image_url": "https://example.com/f.png"},
        )
        video_resp = client.post(
            "/api/images/generate-video-wan-character",
            json={"prompt": "v", "image_url": "https://example.com/i.png"},
        )
        voice_resp = client.post(
            "/api/images/voice/request-note",
            json={"session_id": "sess_100"},
        )

    assert image_resp.status_code == 200
    assert video_resp.status_code == 200
    assert voice_resp.status_code == 200
    usage_types = [call.kwargs.get("usage_type") for call in mock_deduct.await_args_list]
    assert usage_types.count("image") == 1
    assert usage_types.count("video") == 1
    assert usage_types.count("voice") == 1
