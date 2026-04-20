import redis.asyncio as redis
from typing import Optional
import json

from app.core.config import settings


class RedisClient:
    _instance: Optional["RedisClient"] = None
    _client: Optional[redis.Redis] = None

    def __new__(cls) -> "RedisClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self) -> None:
        if self._client is None:
            self._client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )

    async def disconnect(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            raise RuntimeError("Redis not connected")
        return self._client

    async def get(self, key: str) -> Optional[str]:
        return await self.client.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> None:
        await self.client.set(key, value, ex=ex)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    async def get_json(self, key: str) -> Optional[dict]:
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None

    async def set_json(self, key: str, value: dict, ex: Optional[int] = None) -> None:
        await self.set(key, json.dumps(value), ex=ex)

    async def publish(self, channel: str, message: str) -> None:
        await self.client.publish(channel, message)

    async def subscribe(self, channel: str) -> redis.client.PubSub:
        pubsub = self.client.pubsub()
        await pubsub.subscribe(channel)
        return pubsub

    async def lpush(self, name: str, value: str) -> int:
        return await self.client.lpush(name, value)

    async def rpop(self, name: str) -> Optional[str]:
        return await self.client.rpop(name)

    async def lrange(self, name: str, start: int, end: int) -> list[str]:
        return await self.client.lrange(name, start, end)

    async def expire(self, name: str, time: int) -> bool:
        return await self.client.expire(name, time)


redis_client = RedisClient()
