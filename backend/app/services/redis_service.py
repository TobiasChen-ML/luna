import json
import logging
from typing import Optional, Any
from datetime import timedelta
import redis.asyncio as redis
from ..core.config import get_settings

logger = logging.getLogger(__name__)


class RedisService:
    _pool = None
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[redis.Redis] = None
    
    async def _get_client(self) -> redis.Redis:
        if self._client is None:
            if RedisService._pool is None:
                RedisService._pool = redis.ConnectionPool.from_url(
                    self.settings.redis_url,
                    decode_responses=True
                )
            self._client = redis.Redis(connection_pool=RedisService._pool)
        return self._client
    
    async def get(self, key: str) -> Optional[str]:
        client = await self._get_client()
        return await client.get(key)
    
    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        client = await self._get_client()
        serialized = value
        if isinstance(value, (dict, list, tuple)):
            serialized = json.dumps(value)
        elif value is None:
            serialized = ""
        elif not isinstance(value, (str, int, float, bytes)):
            serialized = str(value)
        return await client.set(key, serialized, ex=ex)
    
    async def delete(self, key: str) -> bool:
        client = await self._get_client()
        return bool(await client.delete(key))
    
    async def exists(self, key: str) -> bool:
        client = await self._get_client()
        return bool(await client.exists(key))
    
    async def expire(self, key: str, seconds: int) -> bool:
        client = await self._get_client()
        return await client.expire(key, seconds)
    
    async def ttl(self, key: str) -> int:
        client = await self._get_client()
        return await client.ttl(key)
    
    async def incr(self, key: str) -> int:
        client = await self._get_client()
        return await client.incr(key)
    
    async def decr(self, key: str) -> int:
        client = await self._get_client()
        return await client.decr(key)
    
    async def get_json(self, key: str) -> Optional[dict]:
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None
    
    async def set_json(self, key: str, value: dict, ex: Optional[int] = None) -> bool:
        return await self.set(key, json.dumps(value), ex=ex)
    
    async def publish(self, channel: str, message: str) -> int:
        client = await self._get_client()
        return await client.publish(channel, message)
    
    async def publish_json(self, channel: str, data: dict) -> int:
        return await self.publish(channel, json.dumps(data))
    
    async def subscribe(self, *channels: str):
        client = await self._get_client()
        pubsub = client.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub
    
    async def lpush(self, key: str, value: str) -> int:
        client = await self._get_client()
        return await client.lpush(key, value)
    
    async def rpop(self, key: str) -> Optional[str]:
        client = await self._get_client()
        return await client.rpop(key)
    
    async def llen(self, key: str) -> int:
        client = await self._get_client()
        return await client.llen(key)
    
    async def set_user_profile(self, user_id: int, profile: dict, ex: int = 3600) -> bool:
        return await self.set_json(f"user:profile:{user_id}", profile, ex=ex)
    
    async def get_user_profile(self, user_id: int) -> Optional[dict]:
        return await self.get_json(f"user:profile:{user_id}")
    
    async def set_task_cache(self, task_id: str, data: dict, ex: int = 86400) -> bool:
        return await self.set_json(f"task:{task_id}", data, ex=ex)
    
    async def get_task_cache(self, task_id: str) -> Optional[dict]:
        return await self.get_json(f"task:{task_id}")
    
    async def set_rate_limit(self, key: str, window_seconds: int = 60) -> tuple[int, int]:
        client = await self._get_client()
        current = await client.incr(key)
        if current == 1:
            await client.expire(key, window_seconds)
        ttl = await client.ttl(key)
        return current, ttl
    
    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None
