"""Skills: my, add, remove, not-interested."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user_id
from app.db import get_db
from app.exceptions import APIError
from app.models import Skill, UserSkill, UserNotInterestedSkill

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("/search")
def search_skills(
    q: str = "",
    limit: int = 30,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Search skills by name for manual add (e.g. typeahead)."""
    q = (q or "").strip()
    query = db.query(Skill).filter(Skill.parent_skill_id.is_(None))
    if q:
        query = query.filter(Skill.name.ilike(f"%{q}%"))
    skills = query.limit(min(limit, 50)).all()
    return [{"id": s.id, "name": s.name} for s in skills]


class SkillItem(BaseModel):
    id: int
    name: str
    source: str


class AddSkillIn(BaseModel):
    skill_id: int
    source: str = "manual"


class RemoveSkillIn(BaseModel):
    skill_id: int


class NotInterestedIn(BaseModel):
    skill_id: int
    value: bool


@router.get("/my")
def my_skills(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    rows = db.query(UserSkill, Skill).join(Skill, UserSkill.skill_id == Skill.id).filter(UserSkill.user_id == user_id).all()
    # Return canonical skills user has (by skill_id); if user has a child skill, we show the canonical = parent or self
    result = []
    for us, skill in rows:
        canonical = skill
        if skill.parent_skill_id:
            parent = db.query(Skill).filter(Skill.id == skill.parent_skill_id).first()
            if parent:
                canonical = parent
        result.append({"id": canonical.id, "name": canonical.name, "source": us.source})
    # Dedupe by id
    seen = set()
    out = []
    for r in result:
        if r["id"] not in seen:
            seen.add(r["id"])
            out.append(r)
    return out


@router.post("/add")
def add_skill(data: AddSkillIn, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    skill = db.query(Skill).filter(Skill.id == data.skill_id).first()
    if not skill:
        raise APIError("SKILL_NOT_FOUND", "Skill not found", 404)
    existing = db.query(UserSkill).filter(UserSkill.user_id == user_id, UserSkill.skill_id == data.skill_id).first()
    if existing:
        raise APIError("SKILL_ALREADY_ADDED", "Skill already added", 400)
    db.add(UserSkill(user_id=user_id, skill_id=data.skill_id, source=data.source))
    db.commit()
    return {"ok": True}


@router.post("/remove")
def remove_skill(data: RemoveSkillIn, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    db.query(UserSkill).filter(UserSkill.user_id == user_id, UserSkill.skill_id == data.skill_id).delete()
    db.commit()
    return {"ok": True}


@router.get("/{skill_id}")
def get_skill(skill_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Get skill by id (name, for display)."""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise APIError("SKILL_NOT_FOUND", "Skill not found", 404)
    return {"id": skill.id, "name": skill.name}


@router.post("/not-interested")
def not_interested(data: NotInterestedIn, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    if data.value:
        existing = db.query(UserNotInterestedSkill).filter(
            UserNotInterestedSkill.user_id == user_id, UserNotInterestedSkill.skill_id == data.skill_id
        ).first()
        if not existing:
            db.add(UserNotInterestedSkill(user_id=user_id, skill_id=data.skill_id))
    else:
        db.query(UserNotInterestedSkill).filter(
            UserNotInterestedSkill.user_id == user_id, UserNotInterestedSkill.skill_id == data.skill_id
        ).delete()
    db.commit()
    return {"ok": True}
