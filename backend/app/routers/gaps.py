"""Gaps: missing canonical + mapped skills for role, excluding not-interested."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user_id
from app.db import get_db
from app.exceptions import APIError
import json

from app.models import Role, Skill, UserSkill, UserNotInterestedSkill, RoleAggregate
from app.services.role_analysis import get_or_compute_aggregates

router = APIRouter(tags=["gaps"])


@router.get("/roles/{role_id}/gaps")
def get_gaps(
    role_id: int,
    sort: str = Query("frequency"),
    type_filter: str | None = None,
    search: str | None = None,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise APIError("ROLE_NOT_FOUND", "Role not found", 404)
    data = get_or_compute_aggregates(db, role_id)
    skill_freq = {item["skill_id"]: item for item in data.get("skills", [])}
    user_skill_ids = set()
    for us in db.query(UserSkill).filter(UserSkill.user_id == user_id).all():
        user_skill_ids.add(us.skill_id)
        s = db.query(Skill).filter(Skill.id == us.skill_id).first()
        if s and s.parent_skill_id:
            user_skill_ids.add(s.parent_skill_id)
    not_interested = set(
        n.skill_id for n in db.query(UserNotInterestedSkill).filter(UserNotInterestedSkill.user_id == user_id).all()
    )
    missing_ids = set(skill_freq.keys()) - user_skill_ids - not_interested
    out = []
    for sid in missing_ids:
        s = db.query(Skill).filter(Skill.id == sid).first()
        if not s:
            continue
        if search and search.lower() not in s.name.lower():
            continue
        freq = skill_freq.get(sid, {})
        req = freq.get("required", 0)
        pref = freq.get("preferred", 0)
        desc = freq.get("description", 0)
        skill_type = "required" if req else ("preferred" if pref else "description")
        if type_filter and skill_type != type_filter:
            continue
        frequency = req + pref + desc
        out.append({
            "skill_id": sid,
            "name": s.name,
            "type": skill_type,
            "frequency": frequency,
        })
    if sort == "frequency":
        out.sort(key=lambda x: -x["frequency"])
    elif sort == "name":
        out.sort(key=lambda x: x["name"])
    return out
