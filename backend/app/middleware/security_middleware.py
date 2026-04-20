from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Optional
import logging

from app.services.rate_limit_service import RateLimitService
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    PROTECTED_ENDPOINTS = {
        "/auth/login": {"action": "login", "max_requests": 10, "window_seconds": 60},
        "/auth/register": {"action": "register", "max_requests": 5, "window_seconds": 3600},
        "/auth/verify-email": {"action": "verify_email", "max_requests": 5, "window_seconds": 300},
        "/auth/resend-verification": {"action": "resend_verification", "max_requests": 3, "window_seconds": 300},
        "/auth/refresh": {"action": "refresh_token", "max_requests": 20, "window_seconds": 60},
        "/admin/login": {"action": "admin_login", "max_requests": 5, "window_seconds": 300},
    }
    
    def __init__(self, app, rate_limit_service: Optional[RateLimitService] = None):
        super().__init__(app)
        self.rate_limit = rate_limit_service
        self.settings = get_settings()

    async def dispatch(self, request: Request, call_next):
        path = request.url.path.rstrip("/")
        
        if path in self.PROTECTED_ENDPOINTS:
            config = self.PROTECTED_ENDPOINTS[path]
            client_id = self._get_client_id(request)
            
            try:
                if self.rate_limit is None:
                    self.rate_limit = RateLimitService()
                
                key = f"rate_limit:{config['action']}:{client_id}"
                allowed, remaining, ttl = await self.rate_limit.check_rate_limit(
                    key, config["max_requests"], config["window_seconds"]
                )
                
                if not allowed:
                    logger.warning(
                        f"Rate limit exceeded for {client_id} on {path}"
                    )
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "detail": f"Rate limit exceeded. Retry after {ttl} seconds",
                            "retry_after": ttl
                        },
                        headers={"Retry-After": str(ttl)}
                    )
                
                response = await call_next(request)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Limit"] = str(config["max_requests"])
                response.headers["X-RateLimit-Reset"] = str(ttl)
                return response
                
            except Exception as e:
                logger.error(f"Rate limit check failed: {e}")
                return await call_next(request)
        
        return await call_next(request)

    def _get_client_id(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        if request.client:
            return request.client.host
        
        return "unknown"
