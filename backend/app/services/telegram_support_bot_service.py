import asyncio
import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SupportBotRule:
    keywords: tuple[str, ...]
    answer: str


FAQ_RULES = (
    SupportBotRule(
        keywords=(
            "start",
            "help",
            "menu",
            "mini app",
            "open",
            "\u5165\u53e3",
            "\u83dc\u5355",
            "\u6253\u5f00",
        ),
        answer=(
            "Use the bot menu button to open RoxyClub. I can also answer basic "
            "questions about purchases, credits, account access, and support."
        ),
    ),
    SupportBotRule(
        keywords=(
            "credit",
            "credits",
            "missed",
            "not received",
            "\u4e0d\u5230\u8d26",
            "\u6ca1\u5230\u8d26",
            "\u79ef\u5206",
        ),
        answer=(
            "If credits did not arrive after payment, open the Mini App support page "
            "and submit a ticket with your order details. Our team can check the payment record."
        ),
    ),
    SupportBotRule(
        keywords=(
            "purchase",
            "buy",
            "payment",
            "pay",
            "stars",
            "\u5145\u503c",
            "\u8d2d\u4e70",
            "\u652f\u4ed8",
        ),
        answer=(
            "Purchases are completed in the Telegram Mini App with Telegram Stars. "
            "Open the bot menu, choose the package you want, and follow the Telegram payment prompt."
        ),
    ),
    SupportBotRule(
        keywords=(
            "duplicate",
            "double charge",
            "refund",
            "\u91cd\u590d\u6263\u8d39",
            "\u9000\u6b3e",
            "\u6263\u8d39",
        ),
        answer=(
            "For duplicate charges or refund-related questions, please submit a support "
            "ticket from the Mini App with your order ID or payment screenshot."
        ),
    ),
    SupportBotRule(
        keywords=(
            "safe",
            "privacy",
            "secure",
            "\u5b89\u5168",
            "\u9690\u79c1",
        ),
        answer=(
            "RoxyClub uses account authentication and private account data handling. "
            "Do not share passwords, payment credentials, or sensitive personal details in chat."
        ),
    ),
    SupportBotRule(
        keywords=(
            "web",
            "pwa",
            "benefit",
            "subscription",
            "\u8ba2\u9605",
            "\u4f1a\u5458",
            "\u7f51\u9875",
        ),
        answer=(
            "Paid benefits activated in Telegram can be used on supported Web and PWA flows "
            "after they are linked to your account."
        ),
    ),
    SupportBotRule(
        keywords=(
            "support",
            "customer service",
            "human",
            "ticket",
            "\u5ba2\u670d",
            "\u4eba\u5de5",
            "\u5de5\u5355",
        ),
        answer=(
            "For account-specific help, open the Mini App support page and submit a ticket. "
            "Include your order ID if the question is about billing."
        ),
    ),
)

DEFAULT_SUPPORT_REPLY = (
    "I can help with common RoxyClub questions about the Mini App, payments, credits, "
    "privacy, and support tickets. For account-specific issues, please open the Mini App "
    "support page and submit a ticket."
)


class TelegramSupportBotService:
    def match_answer(self, text: str) -> str:
        normalized = self._normalize_text(text)
        if not normalized:
            return DEFAULT_SUPPORT_REPLY

        for rule in FAQ_RULES:
            if any(keyword in normalized for keyword in rule.keywords):
                return rule.answer

        return DEFAULT_SUPPORT_REPLY

    async def handle_update(self, update: dict[str, Any], *, bot_token: str) -> dict[str, Any]:
        message = update.get("message") or update.get("edited_message") or {}
        text = (message.get("text") or "").strip()
        chat_id = self._extract_chat_id(message)

        if not chat_id or not text:
            return {"handled": False, "reason": "unsupported_update"}

        bind_token = self._extract_bind_token(text)
        if bind_token:
            result = await self._complete_account_bind(bind_token, message)
            await self.send_message(bot_token=bot_token, chat_id=chat_id, text=result["message"])
            return {"handled": True, "action": "telegram_bind", "bound": result["bound"]}

        answer = self.match_answer(text)
        await self.send_message(bot_token=bot_token, chat_id=chat_id, text=answer)
        return {"handled": True}

    async def send_message(self, *, bot_token: str, chat_id: int | str, text: str) -> dict[str, Any]:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        }
        return await self._telegram_api_post(bot_token, "sendMessage", payload)

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join(text.strip().lower().split())

    @staticmethod
    def _extract_chat_id(message: dict[str, Any]) -> Optional[int | str]:
        chat = message.get("chat") or {}
        return chat.get("id")

    @staticmethod
    def _extract_bind_token(text: str) -> Optional[str]:
        parts = text.strip().split(maxsplit=1)
        if len(parts) != 2 or parts[0] != "/start":
            return None
        token = parts[1].strip()
        return token if token.startswith("bind_") else None

    async def _complete_account_bind(self, token: str, message: dict[str, Any]) -> dict[str, Any]:
        from app.models.user import User
        from app.services.database_service import DatabaseService
        from app.services.redis_service import RedisService

        redis = RedisService()
        pending = await redis.get_json(f"telegram:bind:{token}")
        if not pending or not pending.get("user_id"):
            return {
                "bound": False,
                "message": "This Telegram binding link has expired. Please generate a new link from your RoxyClub profile.",
            }

        telegram_user = message.get("from") or {}
        telegram_id = telegram_user.get("id")
        if not telegram_id:
            return {
                "bound": False,
                "message": "Telegram account information was not available. Please try the binding link again.",
            }

        db = DatabaseService()
        user_id = str(pending["user_id"])
        with db.transaction() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "bound": False,
                    "message": "RoxyClub account not found. Please sign in on Web/PWA and create a new binding link.",
                }

            metadata = self._load_user_metadata(getattr(user, "user_metadata", None))
            metadata["telegram"] = {
                "id": str(telegram_id),
                "username": telegram_user.get("username"),
                "first_name": telegram_user.get("first_name"),
                "last_name": telegram_user.get("last_name"),
                "bound_at": datetime.utcnow().isoformat(),
            }
            user.user_metadata = json.dumps(metadata, ensure_ascii=False)

        await redis.delete(f"telegram:bind:{token}")
        return {
            "bound": True,
            "message": "Telegram account linked. Return to RoxyClub Web/PWA and refresh your profile.",
        }

    @staticmethod
    def _load_user_metadata(raw_metadata: Optional[str]) -> dict[str, Any]:
        if not raw_metadata:
            return {}
        try:
            parsed = json.loads(raw_metadata)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            logger.warning("Failed to parse user metadata JSON during Telegram bind")
            return {}

    async def _telegram_api_post(self, bot_token: str, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        api_url = f"https://api.telegram.org/bot{bot_token}/{method}"
        body = json.dumps(payload).encode("utf-8")

        def _request() -> dict[str, Any]:
            req = urllib.request.Request(
                api_url,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read().decode("utf-8")
                return json.loads(data)

        try:
            result = await asyncio.to_thread(_request)
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            logger.error(f"Telegram bot API error [{method}]: HTTP {exc.code} - {error_body}")
            raise ValueError(f"Telegram API HTTP {exc.code}") from exc
        except Exception as exc:
            logger.error(f"Telegram bot API request failed [{method}]: {exc}")
            raise ValueError("Telegram API request failed") from exc

        if not result.get("ok", False):
            logger.error(f"Telegram bot API returned failure [{method}]: {result}")
            raise ValueError(result.get("description") or "Telegram API returned failure")

        return result


telegram_support_bot_service = TelegramSupportBotService()
