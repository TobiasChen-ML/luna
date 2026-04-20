from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Annotated
from functools import lru_cache
import logging

from app.core.config import get_settings, Settings
from app.services.auth_service import jwt_service
from app.services.firebase_service import FirebaseService
from app.models import User

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


@lru_cache
def get_jwt_service():
    return jwt_service


@lru_cache
def get_firebase_service():
    return FirebaseService()


class AuthenticatedUser:
    def __init__(
        self, 
        user_id: str, 
        email: str = "user@example.com", 
        is_admin: bool = False,
        display_name: str = "User",
        firebase_uid: str = None
    ):
        self.id = user_id
        self.email = email
        self.display_name = display_name
        self.avatar_url = None
        self.subscription_tier = "premium" if is_admin else "free"
        self.credits = 1000 if is_admin else 100
        self.is_admin = is_admin
        self.firebase_uid = firebase_uid or user_id


async def get_current_user(
    request: Request,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Optional[User]:
    # Prefer explicit Authorization header; fall back to HttpOnly cookie.
    token: Optional[str] = credentials.credentials if credentials else None
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        return None

    payload = jwt_service.verify_token(token)
    if payload:
        user_id = payload.get("sub")
        email = payload.get("email", "user@example.com")
        is_admin = payload.get("is_admin", False)
        
        return AuthenticatedUser(user_id, email, is_admin)
    
    firebase_service = get_firebase_service()
    if firebase_service._initialized:
        decoded = firebase_service.verify_token(token)
        if decoded:
            user_id = decoded.get("uid")
            email = decoded.get("email", "user@example.com")
            is_admin = email in settings.admin_emails
            
            return AuthenticatedUser(
                user_id=user_id,
                email=email,
                is_admin=is_admin,
                display_name=decoded.get("name", "User"),
                firebase_uid=user_id
            )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="Invalid or expired token"
    )


async def get_current_user_required(
    user: Annotated[Optional[User], Depends(get_current_user)],
) -> User:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Not authenticated"
        )
    return user


async def get_admin_user(
    user: Annotated[User, Depends(get_current_user_required)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    if not getattr(user, 'is_admin', False) and user.email not in settings.admin_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Admin access required"
        )
    return user


async def get_optional_user(
    user: Annotated[Optional[User], Depends(get_current_user)],
) -> Optional[User]:
    return user


async def verify_admin_token(
    authorization: Annotated[Optional[str], Header()] = None
) -> User:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    else:
        token = authorization
    
    payload = jwt_service.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    is_admin = payload.get("is_admin", False)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return AuthenticatedUser(
        payload.get("sub", "admin"),
        payload.get("email", "admin@example.com"),
        is_admin=True
    )


class MockUser:
    """Mock user class for testing purposes."""
    
    def __init__(
        self,
        user_id: str,
        email: str = "test@example.com",
        is_admin: bool = False,
        display_name: str = "Test User",
        firebase_uid: str = None
    ):
        self.id = user_id
        self.email = email
        self.display_name = display_name
        self.avatar_url = None
        self.subscription_tier = "premium" if is_admin else "free"
        self.credits = 1000 if is_admin else 100
        self.is_admin = is_admin
        self.firebase_uid = firebase_uid or user_id


def get_client_info(request: Request) -> dict:
    """Extract client IP and user agent from request."""
    ip_address = request.client.host if request.client else None
    
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        ip_address = real_ip
    
    user_agent = request.headers.get("User-Agent")
    
    return {
        "ip_address": ip_address,
        "user_agent": user_agent,
    }
