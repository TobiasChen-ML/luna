from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from typing import Any
from sse_starlette.sse import EventSourceResponse

from app.models import BaseResponse, NotificationSubscribe, PushNotification

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/stream")
async def notification_stream(request: Request) -> EventSourceResponse:
    async def event_generator():
        yield {"event": "connected", "data": "Connected to notification stream"}
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
