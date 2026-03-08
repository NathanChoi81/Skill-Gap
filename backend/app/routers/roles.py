"""Roles: search, select, analyze, summary."""
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user_id
from app.db import get_db
from app.exceptions import APIError
from app.models import Role, UserRole, UserActiveRole
from app.services.role_analysis import get_or_compute_aggregates

router = APIRouter(prefix="/roles", tags=["roles"])


class SelectRoleIn(BaseModel):
    role_id: int


@router.get("/search")
def search_roles(q: str = "", user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    q = (q or "").strip()
    query = db.query(Role)
    if q:
        query = query.filter(Role.name.ilike(f"%{q}%"))
    roles = query.limit(50).all()
    return [{"id": r.id, "name": r.name} for r in roles]


@router.get("/my")
def my_roles(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """User's role history (roles they have selected), most recent first."""
    rows = (
        db.query(Role, UserRole.last_selected_at)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user_id)
        .order_by(UserRole.last_selected_at.desc().nullslast())
        .limit(20)
        .all()
    )
    return [{"id": r.id, "name": r.name, "last_selected_at": (ts.isoformat() if ts else None)} for r, ts in rows]


@router.post("/select")
def select_role(data: SelectRoleIn, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == data.role_id).first()
    if not role:
        raise APIError("ROLE_NOT_FOUND", "Role not found", 404)
    # Ensure user_roles link
    ur = db.query(UserRole).filter(UserRole.user_id == user_id, UserRole.role_id == data.role_id).first()
    if not ur:
        db.add(UserRole(user_id=user_id, role_id=data.role_id, last_selected_at=datetime.utcnow()))
    else:
        ur.last_selected_at = datetime.utcnow()
    # Set active role
    active = db.query(UserActiveRole).filter(UserActiveRole.user_id == user_id).first()
    if active:
        active.role_id = data.role_id
        active.set_at = datetime.utcnow()
    else:
        db.add(UserActiveRole(user_id=user_id, role_id=data.role_id))
    db.commit()
    return {"ok": True}


@router.post("/{role_id}/analyze")
def analyze_role(role_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise APIError("ROLE_NOT_FOUND", "Role not found", 404)
    get_or_compute_aggregates(db, role_id, force_recompute=True)
    return {"ok": True}


@router.get("/{role_id}/summary")
def role_summary(role_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    from app.services.role_analysis import compute_match_scores
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise APIError("ROLE_NOT_FOUND", "Role not found", 404)
    return compute_match_scores(db, user_id, role_id)
