from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Depends, Response, Body
from typing import Any, Optional
import hashlib
import json
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
from app.services.database_service import DatabaseService
from app.services.redis_service import RedisService
from app.services.credit_service import credit_service
from app.services.firebase_service import FirebaseService
from app.models.credit_transaction import CreditTransaction

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)
db_svc = DatabaseService()
redis_svc = RedisService()

DAILY_CHECKIN_CREDITS = 2


def _has_daily_checkin_transaction(user_id: str, today_key: str) -> bool:
    current_order_id = f"checkin:{user_id}:{today_key}"
    legacy_order_id = f"checkin:{today_key}"
    with db_svc.transaction() as session:
        return session.query(CreditTransaction.id).filter(
            CreditTransaction.user_id == user_id,
            CreditTransaction.transaction_type == "daily_checkin",
            CreditTransaction.order_id.in_([current_order_id, legacy_order_id]),
        ).first() is not None


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _load_user_metadata(raw_metadata: Optional[str]) -> dict[str, Any]:
    if not raw_metadata:
        return {}
    try:
        parsed = json.loads(raw_metadata)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        logger.warning("Failed to parse user metadata JSON")
        return {}


def _extract_telegram_binding(user: Any) -> dict[str, Any]:
    metadata = _load_user_metadata(getattr(user, "user_metadata", None))
    telegram = metadata.get("telegram")
    return telegram if isinstance(telegram, dict) else {}


def _serialize_user(user: Any) -> dict[str, Any]:
    now = datetime.utcnow().isoformat()
    telegram = _extract_telegram_binding(user)
    return {
        "id": user.id,
        "email": user.email,
        "firebase_uid": user.id,
        "display_name": user.display_name or "",
        "subscription_tier": user.tier or "free",
        "credits": float(user.credits or 0),
        "is_adult": True,
        "telegram_id": telegram.get("id"),
        "telegram_username": telegram.get("username"),
        "telegram_bound_at": telegram.get("bound_at"),
        "created_at": user.created_at.isoformat() if getattr(user, "created_at", None) else now,
        "updated_at": user.updated_at.isoformat() if getattr(user, "updated_at", None) else now,
    }


async def _get_user_by_email(email: str):
    return await db_svc.get_user_by_email(email)


@router.post("/register/initiate")
async def register_initiate(
    request: Request,
    data: dict[str, Any]
) -> dict[str, Any]:
    email = _normalize_email(str(data.get("email") or ""))
    password = str(data.get("password") or "")
    if not email:
        raise HTTPException(status_code=400, detail="email required")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="password must be at least 6 characters")

    token = secrets.token_urlsafe(24)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    pending_data = {
        "email": email,
        "password_hash": hashlib.sha256(password.encode("utf-8")).hexdigest(),
        "phone_number": data.get("phone_number"),
        "age_consent_given": bool(data.get("age_consent_given", False)),
        "created_at": datetime.utcnow().isoformat(),
        "status": "pending",
    }
    await redis_svc.set_json(f"auth:verify_token:{token_hash}", pending_data, ex=86400)
    await redis_svc.set_json(f"auth:verify_email:{email}", {"token_hash": token_hash}, ex=86400)

    return {
        "success": True,
        "email": email,
        "message": "Verification initiated",
    }


@router.post("/verify-email")
async def verify_email(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    token = str(data.get("token") or "").strip()
    code = str(data.get("code") or "").strip()
    lookup = token or code
    if not lookup:
        raise HTTPException(status_code=400, detail="token required")

    token_hash = hashlib.sha256(lookup.encode("utf-8")).hexdigest()
    pending = await redis_svc.get_json(f"auth:verify_token:{token_hash}")
    if not pending:
        raise HTTPException(status_code=400, detail="Verification token expired or invalid")

    email = _normalize_email(str(pending.get("email") or ""))
    await redis_svc.set_json(
        f"auth:verified_email:{email}",
        {
            "verified": True,
            "verified_at": datetime.utcnow().isoformat(),
            "token_hash": token_hash,
        },
        ex=86400,
    )
    await redis_svc.delete(f"auth:verify_token:{token_hash}")

    user = await _get_user_by_email(email)
    firebase = FirebaseService()
    custom_token = ""
    if firebase._initialized:
        uid = user.id if user else f"verified_{hashlib.sha256(email.encode('utf-8')).hexdigest()[:16]}"
        generated = firebase.create_custom_token(uid)
        custom_token = generated or ""

    return {
        "success": True,
        "message": "Email verified",
        "customToken": custom_token,
        "user": _serialize_user(user) if user else {
            "id": "",
            "email": email,
            "firebase_uid": "",
            "display_name": "",
            "subscription_tier": "free",
            "credits": 0,
            "is_adult": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        },
    }


@router.post("/resend-verification", response_model=BaseResponse)
async def resend_verification(
    request: Request,
    data: dict[str, Any]
) -> BaseResponse:
    email = _normalize_email(str(data.get("email") or ""))
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
    pending = await redis_svc.get_json(f"auth:verify_email:{email}")
    if pending and pending.get("token_hash"):
        await redis_svc.delete(f"auth:verify_token:{pending.get('token_hash')}")

    token = secrets.token_urlsafe(24)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    await redis_svc.set_json(
        f"auth:verify_token:{token_hash}",
        {"email": email, "created_at": datetime.utcnow().isoformat(), "status": "pending"},
        ex=86400,
    )
    await redis_svc.set_json(f"auth:verify_email:{email}", {"token_hash": token_hash}, ex=86400)
    return BaseResponse(success=True, message="Verification email resent")


@router.post("/register")
async def register(request: Request, response: Response, data: dict[str, Any]) -> dict[str, Any]:
    email = _normalize_email(str(data.get("email") or ""))
    if not email:
        raise HTTPException(status_code=400, detail="email required")

    firebase_uid = str(data.get("firebase_uid") or "").strip()
    user_id = firebase_uid or f"usr_{hashlib.sha256(email.encode('utf-8')).hexdigest()[:20]}"
    display_name = str(data.get("display_name") or "").strip() or email.split("@")[0]
    is_admin = email in get_settings().admin_emails

    user = await _get_user_by_email(email)
    is_new_user = False
    if not user:
        user = await db_svc.create_user(user_id=user_id, email=email, display_name=display_name)
        is_new_user = True
        try:
            await credit_service.grant_signup_bonus(user.id)
        except Exception as exc:
            logger.warning(f"Failed to grant signup bonus for {user.id}: {exc}")

    access_token = jwt_service.create_access_token(user.id, email, is_admin=is_admin)
    refresh_token = jwt_service.create_refresh_token(user.id)
    set_auth_cookies(response, access_token, refresh_token)

    return {
        "success": True,
        "message": "Registration completed",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": _serialize_user(user),
        "is_new_user": is_new_user,
    }


@router.get("/me", response_model=User)
async def get_current_user(
    request: Request,
    user = Depends(get_current_user_required)
) -> User:
    db_user = await db_svc.get_user_by_id(user.id)
    balance = await credit_service.get_balance(user.id)
    now = datetime.utcnow()
    telegram = _extract_telegram_binding(db_user) if db_user else {}

    return User(
        id=user.id,
        email=(db_user.email if db_user else user.email),
        display_name=(db_user.display_name if db_user else user.display_name),
        avatar_url=(db_user.avatar_url if db_user else getattr(user, 'avatar_url', None)),
        subscription_tier=balance.get("subscription_tier") or getattr(user, 'subscription_tier', 'free'),
        credits=balance.get("total", 0),
        is_admin=getattr(user, 'is_admin', False),
        telegram_id=telegram.get("id"),
        telegram_username=telegram.get("username"),
        telegram_bound_at=telegram.get("bound_at"),
        created_at=(db_user.created_at if db_user and db_user.created_at else now),
        updated_at=(db_user.updated_at if db_user else None),
    )


@router.post("/telegram/bind-link")
async def create_telegram_bind_link(
    request: Request,
    user = Depends(get_current_user_required),
) -> dict[str, Any]:
    from app.core.config import get_config_value

    bot_username = (
        await get_config_value("TELEGRAM_BOT_USERNAME")
        or get_settings().telegram_bot_username
        or ""
    ).strip().lstrip("@")
    if not bot_username:
        raise HTTPException(status_code=503, detail="Telegram bot username not configured")

    token = f"bind_{secrets.token_urlsafe(18).replace('-', '_')}"
    await redis_svc.set_json(
        f"telegram:bind:{token}",
        {
            "user_id": user.id,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending",
        },
        ex=900,
    )

    return {
        "success": True,
        "bind_token": token,
        "bind_url": f"https://t.me/{bot_username}?start={token}",
        "expires_in": 900,
    }


@router.get("/telegram/bind-status")
async def get_telegram_bind_status(
    request: Request,
    user = Depends(get_current_user_required),
) -> dict[str, Any]:
    db_user = await db_svc.get_user_by_id(user.id)
    telegram = _extract_telegram_binding(db_user) if db_user else {}
    return {
        "bound": bool(telegram.get("id")),
        "telegram_id": telegram.get("id"),
        "telegram_username": telegram.get("username"),
        "telegram_bound_at": telegram.get("bound_at"),
    }


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


@router.post("/checkin")
async def daily_checkin(
    request: Request,
    user = Depends(get_current_user_required)
) -> dict[str, Any]:
    user_id = str(user.id)
    today_key = datetime.utcnow().strftime("%Y%m%d")
    if _has_daily_checkin_transaction(user_id, today_key):
        raise HTTPException(status_code=429, detail="Already checked in today")

    lock_key = f"auth:checkin:{user_id}:{today_key}"
    redis_lock_set = False
    try:
        if await redis_svc.exists(lock_key):
            raise HTTPException(status_code=429, detail="Already checked in today")
        await redis_svc.set(lock_key, "1", ex=86400)
        redis_lock_set = True
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(f"daily_checkin Redis lock unavailable for user {user_id}: {exc}")

    try:
        await credit_service.add_credits(
            user_id=user_id,
            amount=float(DAILY_CHECKIN_CREDITS),
            transaction_type="daily_checkin",
            credit_source="purchased",
            order_id=f"checkin:{user_id}:{today_key}",
            description=f"Daily check-in reward ({DAILY_CHECKIN_CREDITS} credits)",
        )
    except Exception as exc:
        logger.error(f"daily_checkin failed for user {user_id}: {exc}")
        if redis_lock_set:
            try:
                await redis_svc.delete(lock_key)
            except Exception as redis_exc:
                logger.warning(f"Failed to release daily_checkin Redis lock for user {user_id}: {redis_exc}")
        raise HTTPException(status_code=500, detail="Failed to grant daily check-in credits")

    balance = await credit_service.get_balance(user_id)
    return {
        "success": True,
        "credits_granted": DAILY_CHECKIN_CREDITS,
        "new_balance": float(balance.get("total", 0)),
        "message": "Daily check-in completed",
    }


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
async def login(request: Request, response: Response, data: LoginRequest) -> dict[str, Any]:
    email = _normalize_email(data.email)
    user = await _get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    is_admin = email in get_settings().admin_emails
    access_token = jwt_service.create_access_token(user.id, email, is_admin=is_admin)
    refresh_token = jwt_service.create_refresh_token(user.id)
    set_auth_cookies(response, access_token, refresh_token)

    return {
        "success": True,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": _serialize_user(user),
    }


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
