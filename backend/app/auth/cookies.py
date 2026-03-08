"""Cookie helpers: set/clear HTTP-only cookies for access and refresh tokens."""
from fastapi import Response

from app.config import get_settings

settings = get_settings()


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    secure = settings.cookie_secure
    # path="/" so the cookie is sent for all same-origin requests (e.g. /me), not only /auth/*
    response.set_cookie(
        key=settings.access_token_cookie_name,
        value=access_token,
        httponly=True,
        secure=secure,
        samesite="strict",
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )
    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=secure,
        samesite="strict",
        max_age=settings.refresh_token_expire_days * 24 * 3600,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(settings.access_token_cookie_name, path="/")
    response.delete_cookie(settings.refresh_token_cookie_name, path="/")
