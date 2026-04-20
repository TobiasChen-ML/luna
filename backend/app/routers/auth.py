from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Depends, Response, Body
from typing import Any, Optional
import hashlib
import secrets
import logging

from app.models import BaseResponse, User, UserProfile
from app.models.schemas import (
    LoginRequest, RegisterRequest, AdminLoginRequest,
    FirebaseTokenRequest, RefreshTokenRequest
)
from app.core.dependencies import get_current_user_required, get_admin_user
from app.core.config import get_settings
from app.core.auth_cookies import set_auth_cookies, clear_auth_cookies
from app.services.auth_service import jwt_service

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/register/initiate", response_model=BaseResponse)
async def register_initiate(
    request: Request, 
    data: RegisterRequest
) -> BaseResponse:
    return BaseResponse(success=True, message="Verification email sent")


@router.post("/verify-email", response_model=BaseResponse)
async def verify_email(request: Request, data: dict[str, Any]) -> BaseResponse:
    code = data.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Verification code required")
    return BaseResponse(success=True, message="Email verified")


@router.post("/resend-verification", response_model=BaseResponse)
async def resend_verification(
    request: Request, 
    data: dict[str, Any]
) -> BaseResponse:
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
    return BaseResponse(success=True, message="Verification email resent")


@router.post("/register")
async def register(request: Request, data: RegisterRequest) -> dict[str, Any]:
    raise HTTPException(
        status_code=400,
        detail="Use Firebase client SDK for registration. Send Firebase ID token in Authorization header."
    )


@router.get("/me", response_model=User)
async def get_current_user(
    request: Request,
    user = Depends(get_current_user_required)
) -> User:
    return User(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        subscription_tier=getattr(user, 'subscription_tier', 'free'),
        credits=getattr(user, 'credits', 0),
        is_admin=getattr(user, 'is_admin', False),
        created_at=datetime.now(),
    )


@router.put("/me/profile", response_model=BaseResponse)
async def update_profile(
    request: Request, 
    profile: UserProfile,
    user = Depends(get_current_user_required)
) -> BaseResponse:
    return BaseResponse(success=True, message="Profile updated")


@router.put("/me/preferences", response_model=BaseResponse)
async def update_preferences(
    request: Request, 
    preferences: dict[str, Any],
    user = Depends(get_current_user_required)
) -> BaseResponse:
    return BaseResponse(success=True, message="Preferences updated")


@router.put("/me/mature-preference", response_model=BaseResponse)
async def update_mature_preference(
    request: Request, 
    data: dict[str, Any],
    user = Depends(get_current_user_required)
) -> BaseResponse:
    mature_preference = data.get("mature_preference")
    return BaseResponse(success=True, message="Mature preference updated")


@router.get("/me/preferences", response_model=dict[str, Any])
async def get_preferences(
    request: Request,
    user = Depends(get_current_user_required)
) -> dict[str, Any]:
    return {"theme": "dark", "notifications": True}


@router.post("/checkin", response_model=BaseResponse)
async def daily_checkin(
    request: Request,
    user = Depends(get_current_user_required)
) -> BaseResponse:
    return BaseResponse(success=True, message="Daily check-in completed")


@router.get("/refill-status")
async def get_refill_status(
    request: Request,
    user = Depends(get_current_user_required)
) -> dict[str, Any]:
    return {
        "last_refill": datetime.now().isoformat(),
        "next_refill": datetime.now().isoformat(),
        "credits_refilled": 50,
    }


@router.post("/admin/trigger-daily-refill", response_model=BaseResponse)
async def trigger_daily_refill(
    request: Request,
    admin = Depends(get_admin_user)
) -> BaseResponse:
    return BaseResponse(success=True, message="Daily refill triggered")


@router.post("/complete-registration", response_model=BaseResponse)
async def complete_registration(
    request: Request,
    user = Depends(get_current_user_required)
) -> BaseResponse:
    return BaseResponse(success=True, message="Registration completed")


@router.post("/age-verification/start", response_model=BaseResponse)
async def start_age_verification(
    request: Request,
    user = Depends(get_current_user_required)
) -> BaseResponse:
    return BaseResponse(success=True, message="Age verification started")


@router.get("/age-verification/status")
async def get_age_verification_status(
    request: Request,
    user = Depends(get_current_user_required)
) -> dict[str, Any]:
    return {"status": "pending", "verified": False}


@router.post("/age-verification/webhook", response_model=BaseResponse)
async def age_verification_webhook(request: Request) -> BaseResponse:
    return BaseResponse(success=True, message="Webhook received")


@router.post("/login")
async def login(request: Request, data: LoginRequest) -> dict[str, Any]:
    raise HTTPException(
        status_code=400,
        detail="Use Firebase client SDK for authentication. Send Firebase ID token in Authorization header."
    )


@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    data: Optional[RefreshTokenRequest] = Body(default=None),
) -> dict[str, Any]:
    """
    Refresh access token.

    Accepts the refresh token from either:
    - the HttpOnly ``refresh_token`` cookie (preferred), or
    - a JSON body ``{ "refresh_token": "..." }`` (Telegram / legacy clients).
    """
    token_value = (data.refresh_token if data else None) or request.cookies.get("refresh_token")
    if not token_value:
        raise HTTPException(status_code=400, detail="refresh_token required")

    payload = jwt_service.verify_token(token_value)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Not a refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    access_token = jwt_service.create_access_token(user_id, "user@example.com", is_admin=False)
    new_refresh_token = jwt_service.create_refresh_token(user_id)

    set_auth_cookies(response, access_token, new_refresh_token)

    return {
        "success": True,
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout", response_model=BaseResponse)
async def logout(response: Response) -> BaseResponse:
    """Clear auth cookies (call before Firebase signOut on the client)."""
    clear_auth_cookies(response)
    return BaseResponse(success=True, message="Logged out")


@router.post("/verify-token")
async def verify_firebase_token(
    request: Request,
    response: Response,
    data: FirebaseTokenRequest,
) -> dict[str, Any]:
    from app.services.firebase_service import FirebaseService
    from app.services.database_service import DatabaseService
    from app.services.credit_service import credit_service
    
    token = data.token
    
    firebase_service = FirebaseService()
    if not firebase_service._initialized:
        raise HTTPException(
            status_code=503,
            detail="Firebase authentication not configured. Please set FIREBASE_PROJECT_ID."
        )
    
    decoded = firebase_service.verify_token(token)
    if not decoded:
        raise HTTPException(status_code=401, detail="Invalid or expired Firebase token")
    
    settings = get_settings()
    firebase_uid = decoded.get("uid") or "unknown"
    email = decoded.get("email", "user@example.com")
    display_name = decoded.get("name")
    is_admin = email in settings.admin_emails
    
    db = DatabaseService()
    user = await db.get_user_by_email(email)
    is_new_user = False
    
    if not user:
        user = await db.create_user(
            user_id=firebase_uid,
            email=email,
            display_name=display_name
        )
        is_new_user = True
        logger.info(f"Created new user: {email}")
    
    if is_new_user or not user.signup_bonus_granted:
        try:
            await credit_service.grant_signup_bonus(user.id)
            logger.info(f"Granted signup bonus to user {user.id}")
        except Exception as e:
            logger.error(f"Failed to grant signup bonus: {e}")
    
    app_token = jwt_service.create_access_token(firebase_uid, email, is_admin=is_admin)
    refresh_token = jwt_service.create_refresh_token(firebase_uid)

    set_auth_cookies(response, app_token, refresh_token)

    return {
        "success": True,
        "access_token": app_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "is_admin": is_admin,
        "firebase_uid": firebase_uid,
        "is_new_user": is_new_user,
    }


@router.post("/test-login")
async def test_login(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    """
    Test-only endpoint for E2E testing.
    Returns a valid JWT token for a test user.
    Only available in non-production environments.
    """
    settings = get_settings()
    if settings.environment == "production":
        raise HTTPException(
            status_code=403,
            detail="Test login endpoint disabled in production"
        )
    
    test_admin = data.get("is_admin", False)
    email = data.get("email", "test@test.com")
    user_id = data.get("user_id", "test-user-001")
    
    access_token = jwt_service.create_access_token(user_id, email, is_admin=test_admin)
    refresh_token = jwt_service.create_refresh_token(user_id)
    
    return {
        "success": True,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "is_admin": test_admin,
        "firebase_uid": user_id,
        "user": {
            "id": user_id,
            "email": email,
            "display_name": "Test User",
            "is_admin": test_admin,
            "subscription_tier": "premium" if test_admin else "free",
            "credits": 1000,
            "is_adult": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        },
    }
