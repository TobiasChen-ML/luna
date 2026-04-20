import logging
from typing import Optional
from ..core.config import get_config_value
from .redis_service import RedisService

logger = logging.getLogger(__name__)


class RateLimitService:
    def __init__(self, redis: Optional[RedisService] = None):
        self.redis = redis or RedisService()
    
    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int = 60
    ) -> tuple[bool, int, int]:
        current, ttl = await self.redis.set_rate_limit(key, window_seconds)
        
        if current > max_requests:
            return False, current - 1, ttl
        
        return True, max_requests - current, ttl
    
    async def check_user_rate_limit(
        self,
        user_id: int,
        action: str = "default"
    ) -> tuple[bool, int, int]:
        rate_per_minute = int(await get_config_value("RATE_LIMIT_PER_MINUTE") or "60")
        rate_per_hour = int(await get_config_value("RATE_LIMIT_PER_HOUR") or "1000")
        limits = {
            "default": (rate_per_minute, 60),
            "hourly": (rate_per_hour, 3600),
            "chat": (30, 60),
            "image": (10, 60),
            "video": (5, 60),
        }
        
        max_requests, window = limits.get(action, limits["default"])
        key = f"rate_limit:{action}:{user_id}"
        
        return await self.check_rate_limit(key, max_requests, window)
    
    async def check_ip_rate_limit(
        self,
        ip: str,
        action: str = "default"
    ) -> tuple[bool, int, int]:
        limits = {
            "default": (100, 60),
            "register": (5, 3600),
            "login": (10, 60),
        }
        
        max_requests, window = limits.get(action, limits["default"])
        key = f"rate_limit:ip:{action}:{ip}"
        
        return await self.check_rate_limit(key, max_requests, window)
    
    async def check_email_rate_limit(
        self,
        email: str,
        action: str = "send"
    ) -> tuple[bool, int, int]:
        limits = {
            "send": (5, 300),
            "verify": (3, 3600),
        }
        
        max_requests, window = limits.get(action, limits["send"])
        key = f"rate_limit:email:{action}:{email}"
        
        return await self.check_rate_limit(key, max_requests, window)