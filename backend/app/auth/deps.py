"""Auth dependencies: get current user from access token in cookie or header."""
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.jwt_utils import decode_token
from app.config import get_settings
from app.db import get_db
from app.models import User

settings = get_settings()


def get_current_user_id(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> int:
    """Extract user id from access token. Raises 401 if missing or invalid."""
    token = request.cookies.get(settings.access_token_cookie_name)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user.id


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[int, Depends(get_current_user_id)],
) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_dev(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != "dev":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Dev role required")
    return user
