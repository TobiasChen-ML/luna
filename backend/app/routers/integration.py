from datetime import datetime
from typing import Any
import hashlib
import hmac
import logging
import urllib.parse

from fastapi import APIRouter, Request, HTTPException, Response

from app.core.auth_cookies import set_auth_cookies
from app.core.config import get_settings
from app.models import BaseResponse, BlogPostCreate, BlogPostUpdate
from app.services.auth_service import jwt_service
from app.services.credit_service import credit_service
from app.services.database_service import DatabaseService

logger = logging.getLogger(__name__)
db_svc = DatabaseService()

router = APIRouter(tags=["integration"])


templates_router = APIRouter(prefix="/api/templates", tags=["templates"])


@templates_router.get("")
async def list_templates(request: Request) -> list[dict[str, Any]]:
    return [
        {"id": "template_001", "name": "Default Template", "type": "character"},
    ]


@templates_router.get("/{template_id}")
async def get_template(request: Request, template_id: str) -> dict[str, Any]:
    return {
        "id": template_id,
        "name": "Template",
        "content": "Template content",
        "variables": ["name", "description"],
    }


blog_router = APIRouter(prefix="/api/blog", tags=["blog"])


@blog_router.get("")
async def list_blog_posts(request: Request) -> list[dict[str, Any]]:
    return [
        {
            "id": "post_001",
            "title": "Welcome to Roxy",
            "slug": "welcome-to-roxy",
            "excerpt": "Introduction to our platform",
            "is_published": True,
            "created_at": datetime.now().isoformat(),
        }
    ]


@blog_router.get("/{slug}")
async def get_blog_post(request: Request, slug: str) -> dict[str, Any]:
    return {
        "id": "post_001",
        "title": "Blog Post",
        "slug": slug,
        "content": "Full blog post content...",
        "is_published": True,
        "created_at": datetime.now().isoformat(),
    }


@blog_router.post("", response_model=BaseResponse)
async def create_blog_post(request: Request, data: BlogPostCreate) -> BaseResponse:
    return BaseResponse(success=True, message="Blog post created")


@blog_router.put("/{post_id}", response_model=BaseResponse)
async def update_blog_post(
    request: Request, 
    post_id: str, 
    data: BlogPostUpdate
) -> BaseResponse:
    return BaseResponse(success=True, message="Blog post updated")


@blog_router.delete("/{post_id}", response_model=BaseResponse)
async def delete_blog_post(request: Request, post_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="Blog post deleted")


@blog_router.get("/admin/posts")
async def list_admin_posts(request: Request) -> list[dict[str, Any]]:
    return [
        {
            "id": "post_001",
            "title": "Admin Post",
            "slug": "admin-post",
            "is_published": False,
            "created_at": datetime.now().isoformat(),
        }
    ]


@blog_router.post("/upload/image")
async def upload_blog_image(request: Request) -> dict[str, Any]:
    return {
        "url": "https://example.com/blog/image.jpg",
        "filename": "uploaded_image.jpg",
    }


geo_router = APIRouter(prefix="/api/geo", tags=["geo"])


@geo_router.get("/check")
async def check_geo(request: Request) -> dict[str, Any]:
    """
    Check geographic location and block Chinese IPs.
    Returns allowed=False for China (CN), True for all other countries.
    """
    # Get client IP from various headers
    client_ip = None
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.headers.get("X-Real-Ip") or request.client.host

    # Try to determine country from IP
    country_code = "UNKNOWN"
    country_name = "Unknown"

    try:
        # Check if it's a private/local IP
        if client_ip in ("127.0.0.1", "localhost", "::1") or client_ip.startswith(("10.", "172.16.", "192.168.")):
            country_code = "LOCAL"
            country_name = "Local Development"
        else:
            # For production, use a simple heuristic or external service
            # Here we'll use a basic approach - you might want to use geoip2 or similar
            country_code = _get_country_from_ip(client_ip)
            country_name = _get_country_name(country_code)
    except Exception as e:
        # Log error but fail open (allow access)
        print(f"Geo lookup failed for IP {client_ip}: {e}")
        country_code = "UNKNOWN"
        country_name = "Unknown"

    # Block China (CN), allow all others
    allowed = country_code != "CN"

    return {
        "country_code": country_code,
        "country_name": country_name,
        "allowed": allowed,
        "client_ip": client_ip if client_ip != "127.0.0.1" else None,
    }


def _get_country_from_ip(ip: str) -> str:
    """
    Simple country detection from IP.
    In production, use a proper GeoIP database like MaxMind GeoIP2.
    """
    # This is a simplified implementation
    # For production, consider using:
    # - geoip2 library with MaxMind database
    # - ip-api.com (free tier available)
    # - ipinfo.io
    # - ipgeolocation.io

    # For now, try to use ip-api.com (free, no API key required for non-commercial)
    import urllib.request
    import json

    try:
        # Note: In production, you should cache these results
        req = urllib.request.Request(
            f"http://ip-api.com/json/{ip}?fields=countryCode,country,status",
            headers={"User-Agent": "Roxy-Geo-Check/1.0"},
        )
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read().decode())
            if data.get("status") == "success":
                return data.get("countryCode", "UNKNOWN")
    except Exception:
        pass

    return "UNKNOWN"


def _get_country_name(code: str) -> str:
    """Convert country code to country name."""
    country_names = {
        "CN": "China",
        "US": "United States",
        "TW": "Taiwan",
        "JP": "Japan",
        "KR": "South Korea",
        "GB": "United Kingdom",
        "DE": "Germany",
        "FR": "France",
        "LOCAL": "Local Development",
        "UNKNOWN": "Unknown",
    }
    return country_names.get(code, code)


auth_router = APIRouter(prefix="/api/auth", tags=["auth-telegram"])


def verify_telegram_init_data(init_data: str, bot_token: str) -> dict[str, Any] | None:
    """
    Verify Telegram Mini App initData string.
    
    Returns parsed user data if valid, None if invalid.
    
    See: https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
    """
    if not init_data or not bot_token:
        return None
    
    try:
        parsed = dict(urllib.parse.parse_qsl(init_data))
        hash_value = parsed.pop('hash', None)
        
        if not hash_value:
            logger.warning("Telegram initData missing hash")
            return None
        
        data_check_items = [f"{k}={v}" for k, v in sorted(parsed.items())]
        data_check_string = '\n'.join(data_check_items)
        
        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256,
        ).digest()
        expected_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(hash_value, expected_hash):
            logger.warning("Telegram initData signature mismatch")
            return None
        
        return parsed
    except Exception as e:
        logger.error(f"Telegram initData verification error: {e}")
        return None


def parse_telegram_user(init_data_parsed: dict) -> dict[str, Any] | None:
    """Extract user info from parsed Telegram initData."""
    import json
    
    user_json = init_data_parsed.get('user')
    if not user_json:
        return None
    
    try:
        return json.loads(user_json)
    except json.JSONDecodeError:
        return None


@auth_router.post("/telegram")
async def telegram_auth(request: Request, response: Response, data: dict[str, Any]) -> dict[str, Any]:
    """
    Authenticate Telegram Mini App user.
    
    Request body:
        - init_data: Raw initData string from Telegram WebApp
        - referral_code: Optional referral code
    
    Returns:
        - access_token: App JWT for API authentication
        - refresh_token: Long-lived token for refreshing access
        - user: User object
        - is_new_user: Whether this is a new registration
    """
    from app.core.config import get_config_value
    
    init_data = data.get('init_data')
    if not init_data:
        raise HTTPException(status_code=400, detail="init_data required")
    
    bot_token = await get_config_value("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise HTTPException(
            status_code=503, 
            detail="Telegram authentication not configured"
        )
    
    parsed = verify_telegram_init_data(init_data, bot_token)
    if not parsed:
        raise HTTPException(status_code=401, detail="Invalid Telegram initData")
    
    tg_user = parse_telegram_user(parsed)
    if not tg_user:
        raise HTTPException(status_code=400, detail="User data not found in initData")
    
    tg_user_id = str(tg_user.get('id'))
    username = tg_user.get('username') or f"tg_{tg_user_id}"
    first_name = tg_user.get('first_name', '')
    last_name = tg_user.get('last_name', '')
    display_name = f"{first_name} {last_name}".strip() or username
    photo_url = tg_user.get('photo_url')
    
    user_id = f"telegram_{tg_user_id}"
    email = f"{tg_user_id}@telegram.roxy.ai"
    is_admin = False

    user = await db_svc.get_user_by_id(user_id)
    is_new_user = False
    if not user:
        user = await db_svc.create_user(user_id=user_id, email=email, display_name=display_name)
        is_new_user = True
        try:
            await credit_service.grant_signup_bonus(user.id)
            user = await db_svc.get_user_by_id(user_id) or user
        except Exception as exc:
            logger.warning(f"Failed to grant signup bonus for Telegram user {user.id}: {exc}")
    
    access_token = jwt_service.create_access_token(user_id, email, is_admin=is_admin)
    refresh_token = jwt_service.create_refresh_token(user_id)

    set_auth_cookies(response, access_token, refresh_token)

    user_data = {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name or display_name,
        "avatar_url": photo_url,
        "subscription_tier": user.tier or "free",
        "credits": float(user.credits or 0),
        "telegram_id": tg_user_id,
        "telegram_username": username,
    }
    
    return {
        "success": True,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_data,
        "is_new_user": is_new_user,
    }


creators_router = APIRouter(prefix="/api/creators", tags=["creators"])


@creators_router.get("/{user_id}")
async def get_creator(request: Request, user_id: str) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "username": "creator",
        "display_name": "Content Creator",
        "avatar_url": "https://example.com/avatar.jpg",
        "bio": "Creating amazing content",
        "stats": {
            "characters": 10,
            "scripts": 5,
            "followers": 100,
        },
        "created_at": datetime.now().isoformat(),
    }
