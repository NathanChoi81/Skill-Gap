"""Auth routes: register, login, refresh, logout."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.auth.blacklist import add_to_blacklist, is_blacklisted
from app.exceptions import APIError
from app.auth.cookies import clear_auth_cookies, set_auth_cookies
from app.auth.jwt_utils import create_access_token, create_refresh_token, decode_token
from app.auth.password import hash_password, validate_password_policy, verify_password
from app.config import get_settings
from app.db import get_db
from app.models import User
from app.schemas.common import ErrorResponse

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


class RegisterIn(BaseModel):
    email: EmailStr
    password: str


class RegisterOut(BaseModel):
    user: dict


class LoginIn(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", response_model=RegisterOut)
def register(
    data: RegisterIn,
    response: Response,
    db: Session = Depends(get_db),
):
    ok, msg = validate_password_policy(data.password)
    if not ok:
        raise APIError("AUTH_PASSWORD_POLICY", msg, 400)
    if db.query(User).filter(User.email == data.email).first():
        raise APIError("AUTH_EMAIL_EXISTS", "Email already registered", 409)
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    access = create_access_token({"sub": user.id})
    refresh = create_refresh_token({"sub": user.id})
    set_auth_cookies(response, access, refresh)
    return RegisterOut(user={"id": user.id, "email": user.email})


@router.post("/login")
def login(
    data: LoginIn,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise APIError("AUTH_INVALID_CREDENTIALS", "Invalid credentials", 401)
    access = create_access_token({"sub": user.id})
    refresh = create_refresh_token({"sub": user.id})
    set_auth_cookies(response, access, refresh)
    return {"user": {"id": user.id, "email": user.email}}


@router.post("/refresh")
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    refresh_token = request.cookies.get(settings.refresh_token_cookie_name)
    if not refresh_token:
        raise APIError("AUTH_TOKEN_INVALID", "Missing refresh token", 401)
    if is_blacklisted(db, refresh_token):
        raise APIError("AUTH_TOKEN_INVALID", "Token invalidated", 401)
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise APIError("AUTH_TOKEN_INVALID", "Invalid refresh token", 401)
    user_id = payload.get("sub")
    if user_id is None:
        raise APIError("AUTH_TOKEN_INVALID", "Invalid token", 401)
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise APIError("AUTH_TOKEN_INVALID", "User not found", 401)
    access = create_access_token({"sub": user.id})
    set_auth_cookies(response, access, refresh_token)  # re-set with new access; refresh unchanged (rotation optional)
    return {"ok": True}


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get(settings.refresh_token_cookie_name)
    clear_auth_cookies(response)
    if refresh_token:
        payload = decode_token(refresh_token)
        if payload and payload.get("exp"):
            exp_ts = payload["exp"]
            expires_at = datetime.utcfromtimestamp(exp_ts)
            add_to_blacklist(db, refresh_token, expires_at)
    return {"ok": True}
