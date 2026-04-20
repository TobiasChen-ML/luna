from fastapi import Response

from app.core.config import get_settings


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    access_token_max_age: int = 3600,
) -> None:
    """Set HttpOnly auth cookies on the response.

    Sets three cookies:
    - access_token  (HttpOnly, 1 h)  — carries the JWT, unreadable by JS
    - refresh_token (HttpOnly, 30 d) — scoped to /api/auth/refresh only
    - session_active (JS-readable)  — lets the frontend know a session exists
    """
    settings = get_settings()
    is_secure = settings.environment == "production"

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=access_token_max_age,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=30 * 24 * 3600,
        path="/api/auth/refresh",
    )
    # Non-HttpOnly indicator so JS can detect an active session without
    # being able to read the actual token value.
    response.set_cookie(
        key="session_active",
        value="1",
        httponly=False,
        secure=is_secure,
        samesite="lax",
        max_age=30 * 24 * 3600,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    """Expire all auth cookies (called on logout)."""
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/api/auth/refresh")
    response.delete_cookie(key="session_active", path="/")
