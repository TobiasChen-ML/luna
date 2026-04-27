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
