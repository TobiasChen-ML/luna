import asyncio
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.services.telegram_support_bot_service import TelegramSupportBotService


class TestTelegramSupportBotService:
    def test_match_answer_for_payment_question(self):
        service = TelegramSupportBotService()

        answer = service.match_answer("\u600e\u4e48\u5145\u503c Telegram Stars?")

        assert "Telegram Stars" in answer

    def test_match_answer_prioritizes_missing_credits(self):
        service = TelegramSupportBotService()

        answer = service.match_answer("\u8d2d\u4e70\u6ca1\u5230\u8d26")

        assert "credits did not arrive" in answer

    def test_match_answer_for_unknown_question(self):
        service = TelegramSupportBotService()

        answer = service.match_answer("something unrelated")

        assert "Mini App support page" in answer

    def test_start_sends_welcome_card(self):
        service = TelegramSupportBotService()
        service.send_welcome_card = AsyncMock(return_value={"ok": True})  # type: ignore[method-assign]

        result = asyncio.run(
            service.handle_update(
                {"message": {"text": "/start", "chat": {"id": 12345}}},
                bot_token="test-token",
            )
        )

        assert result == {"handled": True, "action": "welcome"}
        service.send_welcome_card.assert_awaited_once()

    def test_callback_routes_to_recharge_card(self):
        service = TelegramSupportBotService()
        service.answer_callback_query = AsyncMock(return_value={"ok": True})  # type: ignore[method-assign]
        service.send_recharge_card = AsyncMock(return_value={"ok": True})  # type: ignore[method-assign]

        result = asyncio.run(
            service.handle_update(
                {
                    "callback_query": {
                        "id": "callback-1",
                        "data": "recharge",
                        "message": {"chat": {"id": 12345}},
                    }
                },
                bot_token="test-token",
            )
        )

        assert result == {"handled": True, "action": "recharge"}
        service.answer_callback_query.assert_awaited_once()
        service.send_recharge_card.assert_awaited_once()

    def test_character_card_sends_photo_with_chat_button(self, monkeypatch):
        import app.services.character_service as character_service_module

        service = TelegramSupportBotService()
        character = {
            "id": "char_1",
            "name": "Luna",
            "first_name": "Luna",
            "slug": "luna",
            "top_category": "girls",
            "is_official": True,
            "is_public": True,
            "avatar_url": "https://example.com/luna.jpg",
            "personality_summary": "Warm and curious.",
            "personality_tags": ["sweet", "playful"],
        }
        monkeypatch.setattr(
            character_service_module.character_service,
            "get_character_by_id",
            AsyncMock(return_value=character),
        )
        service.send_photo = AsyncMock(return_value={"ok": True})  # type: ignore[method-assign]
        service._web_url = AsyncMock(return_value="https://roxyclub.ai/ai-girlfriend/luna")  # type: ignore[method-assign]

        result = asyncio.run(
            service.send_character_card(
                bot_token="test-token",
                chat_id=12345,
                character_id="char_1",
            )
        )

        assert result == {"ok": True}
        kwargs = service.send_photo.await_args.kwargs
        assert kwargs["photo"] == "https://example.com/luna.jpg"
        assert "Luna" in kwargs["caption"]
        assert kwargs["reply_markup"]["inline_keyboard"][0][0]["url"].endswith("/ai-girlfriend/luna")

    def test_stars_status_uses_telegram_balance(self):
        service = TelegramSupportBotService()
        service._telegram_api_post = AsyncMock(  # type: ignore[method-assign]
            return_value={"ok": True, "result": {"amount": 42}}
        )
        service.send_message = AsyncMock(return_value={"ok": True})  # type: ignore[method-assign]
        service._mini_app_url = AsyncMock(return_value="https://t.me/RoxyClubBot/app?startapp=purchase")  # type: ignore[method-assign]

        asyncio.run(service.send_stars_status(bot_token="test-token", chat_id=12345))

        kwargs = service.send_message.await_args.kwargs
        assert "Bot Star balance: 42" in kwargs["text"]
        assert "Recharge with Stars" in kwargs["reply_markup"]["inline_keyboard"][0][0]["text"]


class TestTelegramBotWebhook:
    def test_webhook_replies_to_text_message(self, client: TestClient, monkeypatch):
        from app.routers import telegram_bot

        async def fake_get_config_value(key: str, default=None):
            if key == "TELEGRAM_BOT_TOKEN":
                return "test-token"
            return default

        send_message = AsyncMock(return_value={"ok": True})
        monkeypatch.setattr(telegram_bot, "get_config_value", fake_get_config_value)
        monkeypatch.setattr(
            telegram_bot.telegram_support_bot_service,
            "send_message",
            send_message,
        )

        response = client.post(
            "/api/telegram/bot/webhook",
            json={
                "message": {
                    "text": "\u8d2d\u4e70\u6ca1\u5230\u8d26",
                    "chat": {"id": 12345},
                }
            },
        )

        assert response.status_code == 200
        assert response.json()["handled"] is True
        send_message.assert_awaited_once()
        assert send_message.await_args.kwargs["chat_id"] == 12345

    def test_webhook_rejects_invalid_secret(self, client: TestClient, monkeypatch):
        from app.routers import telegram_bot

        async def fake_get_config_value(key: str, default=None):
            if key == "TELEGRAM_BOT_WEBHOOK_SECRET":
                return "expected-secret"
            if key == "TELEGRAM_BOT_TOKEN":
                return "test-token"
            return default

        monkeypatch.setattr(telegram_bot, "get_config_value", fake_get_config_value)

        response = client.post(
            "/api/telegram/bot/webhook",
            headers={"X-Telegram-Bot-Api-Secret-Token": "bad-secret"},
            json={"message": {"text": "help", "chat": {"id": 12345}}},
        )

        assert response.status_code == 403

    def test_webhook_ignores_non_text_updates(self, client: TestClient, monkeypatch):
        from app.routers import telegram_bot

        async def fake_get_config_value(key: str, default=None):
            if key == "TELEGRAM_BOT_TOKEN":
                return "test-token"
            return default

        monkeypatch.setattr(telegram_bot, "get_config_value", fake_get_config_value)

        response = client.post("/api/telegram/bot/webhook", json={"my_chat_member": {}})

        assert response.status_code == 200
        assert response.json() == {
            "success": True,
            "handled": False,
            "reason": "unsupported_update",
        }
