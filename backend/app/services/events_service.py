import logging
import json
from datetime import datetime
from typing import Optional, AsyncIterator
import asyncio

from ..core.config import get_settings
from .redis_service import RedisService
from .database_service import DatabaseService

logger = logging.getLogger(__name__)


class EventsService:
    EVENT_CHANNELS = {
        "user": "events:user",
        "session": "events:session",
        "task": "events:task",
        "notification": "events:notification",
    }

    def __init__(
        self,
        redis: Optional[RedisService] = None,
        db: Optional[DatabaseService] = None,
    ):
        self.settings = get_settings()
        self.redis = redis or RedisService()
        self.db = db or DatabaseService()

    async def subscribe_to_user_events(
        self,
        user_id: str,
    ) -> AsyncIterator[dict]:
        channel = f"{self.EVENT_CHANNELS['user']}:{user_id}"
        
        pubsub = await self.redis.subscribe(channel)
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    yield {
                        "event": data.get("event_type"),
                        "data": data.get("payload"),
                        "timestamp": data.get("timestamp"),
                    }
        finally:
            await pubsub.unsubscribe(channel)

    async def subscribe_to_session_events(
        self,
        session_id: str,
    ) -> AsyncIterator[dict]:
        channel = f"{self.EVENT_CHANNELS['session']}:{session_id}"
        
        pubsub = await self.redis.subscribe(channel)
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    yield {
                        "event": data.get("event_type"),
                        "data": data.get("payload"),
                        "timestamp": data.get("timestamp"),
                    }
        finally:
            await pubsub.unsubscribe(channel)

    async def publish_event(
        self,
        event_type: str,
        payload: dict,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict:
        event_data = {
            "event_type": event_type,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "session_id": session_id,
        }
        
        if user_id:
            channel = f"{self.EVENT_CHANNELS['user']}:{user_id}"
            await self.redis.publish(channel, json.dumps(event_data))
        
        if session_id:
            channel = f"{self.EVENT_CHANNELS['session']}:{session_id}"
            await self.redis.publish(channel, json.dumps(event_data))
        
        await self.redis.lpush(
            f"events:history:{user_id or 'global'}",
            json.dumps(event_data),
        )
        
        return {"published": True, "event_type": event_type}

    async def publish_task_update(
        self,
        task_id: str,
        status: str,
        progress: float,
        result_url: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> dict:
        return await self.publish_event(
            event_type="task_update",
            payload={
                "task_id": task_id,
                "status": status,
                "progress": progress,
                "result_url": result_url,
            },
            user_id=user_id,
        )

    async def publish_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        data: Optional[dict] = None,
    ) -> dict:
        notification_id = f"notif_{datetime.utcnow().timestamp()}"
        
        await self.redis.set(
            f"notification:{notification_id}",
            {
                "id": notification_id,
                "user_id": user_id,
                "title": title,
                "body": body,
                "data": data or {},
                "read": False,
                "created_at": datetime.utcnow().isoformat(),
            },
            ex=86400 * 7,
        )
        
        return await self.publish_event(
            event_type="notification",
            payload={
                "id": notification_id,
                "title": title,
                "body": body,
                "data": data,
            },
            user_id=user_id,
        )

    async def get_user_notifications(
        self,
        user_id: str,
        limit: int = 20,
        unread_only: bool = False,
    ) -> list[dict]:
        notifications = []
        
        events = await self.redis.lrange(
            f"events:history:{user_id}",
            0,
            limit - 1,
        )
        
        for event_str in events:
            try:
                event = json.loads(event_str)
                if event.get("event_type") == "notification":
                    notifications.append(event.get("payload"))
            except json.JSONDecodeError:
                continue
        
        return notifications

    async def mark_notification_read(self, notification_id: str) -> dict:
        cached = await self.redis.get(f"notification:{notification_id}")
        
        if cached:
            cached["read"] = True
            await self.redis.set(
                f"notification:{notification_id}",
                cached,
                ex=86400 * 7,
            )
        
        return {"notification_id": notification_id, "read": True}

    async def subscribe_push(
        self,
        user_id: str,
        endpoint: str,
        keys: dict,
    ) -> dict:
        await self.redis.set(
            f"push_subscription:{user_id}",
            {
                "user_id": user_id,
                "endpoint": endpoint,
                "keys": keys,
                "created_at": datetime.utcnow().isoformat(),
            },
        )
        
        return {"subscribed": True, "user_id": user_id}

    async def unsubscribe_push(self, user_id: str) -> dict:
        await self.redis.delete(f"push_subscription:{user_id}")
        
        return {"unsubscribed": True, "user_id": user_id}

    async def get_push_subscription(self, user_id: str) -> Optional[dict]:
        return await self.redis.get(f"push_subscription:{user_id}")

    async def send_push_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        data: Optional[dict] = None,
    ) -> dict:
        subscription = await self.get_push_subscription(user_id)
        
        if not subscription:
            return {"sent": False, "reason": "No subscription found"}
        
        return {
            "sent": True,
            "user_id": user_id,
            "endpoint": subscription.get("endpoint"),
        }

    async def send_test_event(self, user_id: str) -> dict:
        return await self.publish_event(
            event_type="test",
            payload={"message": "Test event"},
            user_id=user_id,
        )

    async def health_check(self) -> dict:
        return {
            "status": "healthy",
            "channels": list(self.EVENT_CHANNELS.keys()),
        }