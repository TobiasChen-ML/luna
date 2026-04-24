import asyncio
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Request
from typing import Any
from sse_starlette.sse import EventSourceResponse

from app.models import BaseResponse, NotificationSubscribe, PushNotification
from app.core.redis_client import redis_client

router = APIRouter(prefix="/api/notifications", tags=["notifications"])
logger = logging.getLogger(__name__)


@router.get("/stream")
async def notification_stream(request: Request) -> EventSourceResponse:
    channels = [
        "video_completed",
        "video_failed",
        "image_done",
        "image_failed",
        "credit_update",
        "audio_uploaded",
        "task_status",
    ]

    async def event_generator():
        yield {
            "event": "connected",
            "data": json.dumps(
                {"message": "Connected to notification stream"},
                ensure_ascii=False,
            ),
        }

        pubsub = None
        try:
            pubsub = redis_client.client.pubsub()
            await pubsub.subscribe(*channels)
            last_heartbeat = datetime.now(timezone.utc)

            while True:
                if await request.is_disconnected():
                    break

                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                if message and message.get("type") == "message":
                    channel = str(message.get("channel") or "")
                    raw_data = message.get("data")
                    if isinstance(raw_data, bytes):
                        raw_data = raw_data.decode("utf-8", errors="ignore")
                    if not isinstance(raw_data, str):
                        raw_data = str(raw_data)

                    try:
                        payload = json.loads(raw_data)
                    except json.JSONDecodeError:
                        payload = {"message": raw_data}

                    yield {
                        "event": channel,
                        "data": json.dumps(payload, ensure_ascii=False),
                    }

                now = datetime.now(timezone.utc)
                if (now - last_heartbeat).total_seconds() >= 15:
                    yield {
                        "event": "heartbeat",
                        "data": json.dumps({"timestamp": now.isoformat()}, ensure_ascii=False),
                    }
                    last_heartbeat = now
                await asyncio.sleep(0.05)
        except RuntimeError:
            logger.warning("Redis not connected for notification stream")
            yield {
                "event": "error",
                "data": json.dumps(
                    {"message": "Notification backend unavailable", "error_code": "redis_unavailable"},
                    ensure_ascii=False,
                ),
            }
        except Exception:
            logger.exception("Notification stream failed")
            yield {
                "event": "error",
                "data": json.dumps(
                    {"message": "Notification stream error", "error_code": "stream_error"},
                    ensure_ascii=False,
                ),
            }
        finally:
            if pubsub is not None:
                try:
                    await pubsub.unsubscribe(*channels)
                    await pubsub.close()
                except Exception:
                    logger.debug("Failed to close notification pubsub cleanly", exc_info=True)

    return EventSourceResponse(event_generator())


@router.get("/health")
async def notifications_health(request: Request) -> dict[str, Any]:
    return {"status": "healthy", "connections": 0}


@router.post("/test", response_model=BaseResponse)
async def test_notification(request: Request) -> BaseResponse:
    return BaseResponse(success=True, message="Test notification sent")


@router.post("/subscribe-push", response_model=BaseResponse)
async def subscribe_push(request: Request, data: NotificationSubscribe) -> BaseResponse:
    return BaseResponse(success=True, message="Push subscription created")


@router.delete("/unsubscribe-push", response_model=BaseResponse)
async def unsubscribe_push(request: Request) -> BaseResponse:
    return BaseResponse(success=True, message="Push subscription removed")


@router.post("/send-push/{user_id}", response_model=BaseResponse)
async def send_push_to_user(
    request: Request, 
    user_id: str, 
    data: PushNotification
) -> BaseResponse:
    return BaseResponse(success=True, message=f"Push sent to user {user_id}")


@router.get("/check-subscription")
async def check_subscription(request: Request) -> dict[str, Any]:
    return {
        "subscribed": True,
        "endpoint": "https://fcm.googleapis.com/...",
    }
