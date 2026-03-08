"""User route: GET /me."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db import get_db
from app.models import User, UserActiveRole

router = APIRouter(tags=["users"])


class MeOut(BaseModel):
    id: int
    email: str
    active_role_id: int | None
    role: str = "user"


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    active = db.query(UserActiveRole).filter(UserActiveRole.user_id == user.id).first()
    return MeOut(
        id=user.id,
        email=user.email,
        active_role_id=active.role_id if active else None,
        role=user.role or "user",
    )
