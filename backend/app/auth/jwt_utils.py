"""JWT creation and verification for access and refresh tokens."""
from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from app.config import get_settings

settings = get_settings()


def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    # Ensure subject is a string as required by python-jose
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode["exp"] = expire
    to_encode["type"] = "access"
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def create_refresh_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    # Ensure subject is a string as required by python-jose
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode["exp"] = expire
    to_encode["type"] = "refresh"
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return payload
    except JWTError:
        return None
