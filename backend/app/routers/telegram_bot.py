import logging
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException

from app.core.config import get_config_value
from app.services.telegram_support_bot_service import telegram_support_bot_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/telegram/bot", tags=["telegram-bot"])


@router.post("/webhook")
async def telegram_bot_webhook(
    data: dict[str, Any],
    x_telegram_bot_api_secret_token: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    expected_secret = await get_config_value("TELEGRAM_BOT_WEBHOOK_SECRET")
    if expected_secret and x_telegram_bot_api_secret_token != expected_secret:
        raise HTTPException(status_code=403, detail="Invalid Telegram webhook secret")

    bot_token = await get_config_value("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("Telegram bot token not configured")
        raise HTTPException(status_code=503, detail="Telegram bot token not configured")

    try:
        result = await telegram_support_bot_service.handle_update(data, bot_token=bot_token)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"success": True, **result}
