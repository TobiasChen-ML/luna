import asyncio
import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from urllib.parse import quote

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

WELCOME_TEXT = (
    "Welcome to RoxyClub.\n\n"
    "Open the Mini App to chat with AI companions, buy credits with Telegram Stars, "
    "or browse featured characters here first."
)

RECHARGE_TEXT = (
    "Credits and subscriptions are purchased in the Telegram Mini App with Telegram Stars.\n\n"
    "Tap Recharge to open the billing page. If you already paid and credits did not arrive, "
    "use Support and include your order details."
)

CHARACTER_LIST_TEXT = "Pick a character to preview. You can open the Mini App from any character card."

STAR_BALANCE_HELP_TEXT = (
    "Telegram does not expose a user's personal Star wallet balance to bots. "
    "I can show bot-side Star balance when available, and you can manage purchases in the Mini App."
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
        callback_query = update.get("callback_query")
        if isinstance(callback_query, dict):
            return await self._handle_callback_query(callback_query, bot_token=bot_token)

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

        normalized = self._normalize_text(text)
        if normalized.startswith("/start") or normalized in {"/menu", "menu", "start", "help", "/help"}:
            await self.send_welcome_card(bot_token=bot_token, chat_id=chat_id)
            return {"handled": True, "action": "welcome"}

        if normalized in {"/recharge", "recharge", "top up", "\u5145\u503c", "\u8d2d\u4e70", "buy"}:
            await self.send_recharge_card(bot_token=bot_token, chat_id=chat_id)
            return {"handled": True, "action": "recharge"}

        if normalized in {"/characters", "characters", "browse", "\u89d2\u8272", "\u770b\u89d2\u8272", "\u9009\u89d2\u8272"}:
            await self.send_character_list(bot_token=bot_token, chat_id=chat_id)
            return {"handled": True, "action": "characters"}

        if normalized in {"/stars", "stars", "star", "\u67e5\u8be2star", "\u67e5\u8be2stars"}:
            await self.send_stars_status(bot_token=bot_token, chat_id=chat_id)
            return {"handled": True, "action": "stars"}

        answer = self.match_answer(text)
        await self.send_message(
            bot_token=bot_token,
            chat_id=chat_id,
            text=answer,
            reply_markup=await self._main_menu_keyboard(),
        )
        return {"handled": True, "action": "faq"}

    async def send_message(
        self,
        *,
        bot_token: str,
        chat_id: int | str,
        text: str,
        reply_markup: Optional[dict[str, Any]] = None,
        parse_mode: Optional[str] = None,
    ) -> dict[str, Any]:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        if parse_mode:
            payload["parse_mode"] = parse_mode
        return await self._telegram_api_post(bot_token, "sendMessage", payload)

    async def send_welcome_card(self, *, bot_token: str, chat_id: int | str) -> dict[str, Any]:
        card_image_url = await self._config_value("TELEGRAM_BOT_CARD_IMAGE_URL", "")
        reply_markup = await self._main_menu_keyboard()
        if card_image_url:
            return await self.send_photo(
                bot_token=bot_token,
                chat_id=chat_id,
                photo=card_image_url,
                caption=WELCOME_TEXT,
                reply_markup=reply_markup,
            )
        return await self.send_message(
            bot_token=bot_token,
            chat_id=chat_id,
            text=WELCOME_TEXT,
            reply_markup=reply_markup,
        )

    async def send_recharge_card(self, *, bot_token: str, chat_id: int | str) -> dict[str, Any]:
        return await self.send_message(
            bot_token=bot_token,
            chat_id=chat_id,
            text=RECHARGE_TEXT,
            reply_markup={
                "inline_keyboard": [
                    [{"text": "Recharge with Stars", "url": await self._mini_app_url("purchase")}],
                    [{"text": "Check Stars", "callback_data": "stars"}],
                    [{"text": "Support", "url": await self._mini_app_url("support")}],
                ]
            },
        )

    async def send_character_list(
        self,
        *,
        bot_token: str,
        chat_id: int | str,
        top_category: str = "girls",
    ) -> dict[str, Any]:
        from app.services.character_service import character_service

        characters, _ = await character_service.list_official_characters(
            top_category=top_category,
            page=1,
            page_size=6,
        )
        rows: list[list[dict[str, str]]] = []
        for character in characters:
            name = self._character_name(character)
            rows.append([{"text": name[:32], "callback_data": f"char:{character['id']}"}])

        category_row = [
            {"text": "Girls", "callback_data": "browse:girls"},
            {"text": "Anime", "callback_data": "browse:anime"},
            {"text": "Guys", "callback_data": "browse:guys"},
        ]
        rows.append(category_row)
        rows.append([{"text": "Open Mini App", "url": await self._mini_app_url(f"browse_{top_category}")}])

        text = CHARACTER_LIST_TEXT
        if not characters:
            text = "No featured characters are available right now. Open the Mini App to continue."

        return await self.send_message(
            bot_token=bot_token,
            chat_id=chat_id,
            text=text,
            reply_markup={"inline_keyboard": rows},
        )

    async def send_character_card(
        self,
        *,
        bot_token: str,
        chat_id: int | str,
        character_id: str,
    ) -> dict[str, Any]:
        from app.services.character_service import character_service

        character = await character_service.get_character_by_id(character_id)
        if not character or not character.get("is_official") or not character.get("is_public"):
            return await self.send_message(
                bot_token=bot_token,
                chat_id=chat_id,
                text="This character is not available. Please choose another one.",
                reply_markup={"inline_keyboard": [[{"text": "Browse Characters", "callback_data": "browse:girls"}]]},
            )

        name = self._character_name(character)
        caption = self._format_character_caption(character)
        image_url = self._character_image_url(character)
        reply_markup = {
            "inline_keyboard": [
                [{"text": f"Chat with {name[:20]}", "url": await self._character_chat_url(character)}],
                [{"text": "More Characters", "callback_data": f"browse:{character.get('top_category') or 'girls'}"}],
                [{"text": "Recharge", "callback_data": "recharge"}],
            ]
        }

        if image_url:
            return await self.send_photo(
                bot_token=bot_token,
                chat_id=chat_id,
                photo=image_url,
                caption=caption,
                reply_markup=reply_markup,
            )
        return await self.send_message(
            bot_token=bot_token,
            chat_id=chat_id,
            text=caption,
            reply_markup=reply_markup,
        )

    async def send_stars_status(self, *, bot_token: str, chat_id: int | str) -> dict[str, Any]:
        text = STAR_BALANCE_HELP_TEXT
        try:
            result = await self._telegram_api_post(bot_token, "getMyStarBalance", {})
            balance = result.get("result")
            amount = balance.get("amount") if isinstance(balance, dict) else balance
            if amount is not None:
                text = f"Bot Star balance: {amount}\n\n{STAR_BALANCE_HELP_TEXT}"
        except ValueError:
            logger.warning("Telegram Star balance lookup failed")

        return await self.send_message(
            bot_token=bot_token,
            chat_id=chat_id,
            text=text,
            reply_markup={
                "inline_keyboard": [
                    [{"text": "Recharge with Stars", "url": await self._mini_app_url("purchase")}],
                    [{"text": "Support", "url": await self._mini_app_url("support")}],
                ]
            },
        )

    async def send_photo(
        self,
        *,
        bot_token: str,
        chat_id: int | str,
        photo: str,
        caption: str,
        reply_markup: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "photo": photo,
            "caption": caption[:1024],
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return await self._telegram_api_post(bot_token, "sendPhoto", payload)

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

    async def _handle_callback_query(self, callback_query: dict[str, Any], *, bot_token: str) -> dict[str, Any]:
        callback_id = callback_query.get("id")
        data = str(callback_query.get("data") or "")
        message = callback_query.get("message") or {}
        chat_id = self._extract_chat_id(message)
        if callback_id:
            await self.answer_callback_query(bot_token=bot_token, callback_query_id=callback_id)

        if not chat_id or not data:
            return {"handled": False, "reason": "unsupported_callback"}

        if data == "menu":
            await self.send_welcome_card(bot_token=bot_token, chat_id=chat_id)
            return {"handled": True, "action": "welcome"}
        if data == "recharge":
            await self.send_recharge_card(bot_token=bot_token, chat_id=chat_id)
            return {"handled": True, "action": "recharge"}
        if data == "stars":
            await self.send_stars_status(bot_token=bot_token, chat_id=chat_id)
            return {"handled": True, "action": "stars"}
        if data.startswith("browse:"):
            category = data.split(":", 1)[1] or "girls"
            await self.send_character_list(bot_token=bot_token, chat_id=chat_id, top_category=category)
            return {"handled": True, "action": "characters", "category": category}
        if data.startswith("char:"):
            character_id = data.split(":", 1)[1]
            await self.send_character_card(bot_token=bot_token, chat_id=chat_id, character_id=character_id)
            return {"handled": True, "action": "character_card", "character_id": character_id}

        await self.send_message(bot_token=bot_token, chat_id=chat_id, text=DEFAULT_SUPPORT_REPLY)
        return {"handled": True, "action": "fallback"}

    async def answer_callback_query(
        self,
        *,
        bot_token: str,
        callback_query_id: str,
        text: Optional[str] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        return await self._telegram_api_post(bot_token, "answerCallbackQuery", payload)

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

    @staticmethod
    def _character_name(character: dict[str, Any]) -> str:
        return str(character.get("first_name") or character.get("name") or "Character")

    @staticmethod
    def _character_image_url(character: dict[str, Any]) -> str:
        for field in ("avatar_card_url", "profile_image_url", "avatar_url", "cover_url"):
            value = str(character.get(field) or "").strip()
            if value.startswith("http://") or value.startswith("https://"):
                return value
        return ""

    def _format_character_caption(self, character: dict[str, Any]) -> str:
        name = self._character_name(character)
        age = character.get("age")
        occupation = str(character.get("occupation") or "").strip()
        summary = str(character.get("personality_summary") or character.get("description") or "").strip()
        tags = character.get("personality_tags") or character.get("filter_tags") or []
        tag_text = ", ".join(str(tag) for tag in tags[:3]) if isinstance(tags, list) else ""

        lines = [name]
        details = [str(age) if age else "", occupation]
        details_text = " - ".join(item for item in details if item)
        if details_text:
            lines.append(details_text)
        if summary:
            lines.append(summary[:240])
        if tag_text:
            lines.append(f"Tags: {tag_text}")
        return "\n\n".join(lines)

    async def _character_chat_url(self, character: dict[str, Any]) -> str:
        slug = str(character.get("slug") or "").strip()
        category = str(character.get("top_category") or "girls")
        prefix = {"anime": "ai-anime", "guys": "ai-boyfriend", "girls": "ai-girlfriend"}.get(category, "ai-girlfriend")
        if slug:
            return await self._web_url(f"/{prefix}/{quote(slug)}")
        return await self._mini_app_url(f"character_{character.get('id')}")

    async def _web_url(self, path: str = "") -> str:
        base = await self._config_value("ROXY_WEB_APP_URL", "")
        if not base:
            base = await self._config_value("FRONTEND_URL", "https://roxyclub.ai")
        return f"{base.rstrip('/')}/{path.lstrip('/')}" if path else base.rstrip("/")

    async def _mini_app_url(self, start_param: str = "home") -> str:
        mini_app_url = await self._config_value("TELEGRAM_MINI_APP_URL", "")
        safe_start = self._normalize_start_param(start_param)
        if mini_app_url:
            separator = "&" if "?" in mini_app_url else "?"
            return f"{mini_app_url}{separator}startapp={quote(safe_start)}"

        bot_username = (await self._config_value("TELEGRAM_BOT_USERNAME", "")).lstrip("@")
        short_name = await self._config_value("TELEGRAM_MINI_APP_SHORT_NAME", "")
        if bot_username and short_name:
            return f"https://t.me/{bot_username}/{short_name}?startapp={quote(safe_start)}"
        if bot_username:
            return f"https://t.me/{bot_username}?start={quote(safe_start)}"
        return await self._web_url("/")

    @staticmethod
    def _normalize_start_param(start_param: str) -> str:
        normalized = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in start_param)
        return normalized[:512] or "home"

    async def _config_value(self, key: str, default: str) -> str:
        from app.core.config import get_config_value

        value = await get_config_value(key, default)
        return str(value or default).strip()

    async def _main_menu_keyboard(self) -> dict[str, Any]:
        return {
            "inline_keyboard": [
                [{"text": "Open Mini App", "url": await self._mini_app_url("home")}],
                [
                    {"text": "Browse Characters", "callback_data": "browse:girls"},
                    {"text": "Recharge", "callback_data": "recharge"},
                ],
                [
                    {"text": "Check Stars", "callback_data": "stars"},
                    {"text": "Support", "url": await self._mini_app_url("support")},
                ],
            ]
        }

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
