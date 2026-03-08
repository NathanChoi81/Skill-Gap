"""Plan: propose, confirm, current."""
from datetime import date, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.deps import get_current_user_id
from app.db import get_db
from app.exceptions import APIError
from app.models import Plan, PlanSkill, PlanSkillCourse, UserActiveRole
from app.services.plan import propose_plan
from sqlalchemy.orm import Session

router = APIRouter(prefix="/plan", tags=["plan"])


class ProposeIn(BaseModel):
    deadline: str  # YYYY-MM-DD
    hours_per_week: int = 5


class ConfirmIn(BaseModel):
    skills: list[int]
    ordering: list[int]  # skill_ids in order
    deadline: str | None = None  # YYYY-MM-DD from propose step
    hours_per_week: int = 5


@router.post("/propose")
def plan_propose(
    data: ProposeIn,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        d = date.fromisoformat(data.deadline)
    except ValueError:
        raise APIError("PLAN_INVALID_DEADLINE", "Invalid date format (use YYYY-MM-DD)", 400)
    if (d - date.today()).days < 7:
        raise APIError("PLAN_INVALID_DEADLINE", "Deadline must be at least 7 days from today", 400)
    if not 1 <= data.hours_per_week <= 40:
        raise APIError("PLAN_INVALID_HOURS_PER_WEEK", "hours_per_week must be 1-40", 400)
    active = db.query(UserActiveRole).filter(UserActiveRole.user_id == user_id).first()
    if not active or not active.role_id:
        raise APIError("ROLE_NOT_ANALYZED", "Select and analyze a role first", 400)
    return propose_plan(db, user_id, active.role_id, d, data.hours_per_week)


@router.post("/confirm")
def plan_confirm(
    data: ConfirmIn,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    active = db.query(UserActiveRole).filter(UserActiveRole.user_id == user_id).first()
    if not active or not active.role_id:
        raise APIError("ROLE_NOT_ANALYZED", "Select a role first", 400)
    # Create or replace plan
    existing = db.query(Plan).filter(Plan.user_id == user_id, Plan.role_id == active.role_id).first()
    if existing:
        db.query(PlanSkillCourse).filter(PlanSkillCourse.plan_id == existing.id).delete()
        db.query(PlanSkill).filter(PlanSkill.plan_id == existing.id).delete()
        db.delete(existing)
        db.commit()
    from datetime import timedelta
    if data.deadline:
        try:
            deadline_date = date.fromisoformat(data.deadline)
        except ValueError:
            deadline_date = date.today() + timedelta(days=90)
    else:
        deadline_date = date.today() + timedelta(days=90)
    hours_per_week = max(1, min(40, data.hours_per_week))
    plan = Plan(user_id=user_id, role_id=active.role_id, deadline_date=deadline_date, hours_per_week=hours_per_week, status="active")
    db.add(plan)
    db.flush()
    for pos, skill_id in enumerate(data.ordering):
        if skill_id in data.skills:
            db.add(PlanSkill(plan_id=plan.id, skill_id=skill_id, position=pos))
    db.commit()
    return {"plan_id": plan.id, "ok": True}


class PlanStatusIn(BaseModel):
    status: str  # active | paused


@router.patch("/current")
def plan_update_status(
    data: PlanStatusIn,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if data.status not in ("active", "paused"):
        raise APIError("PLAN_STATUS_INVALID", "status must be active or paused", 400)
    active = db.query(UserActiveRole).filter(UserActiveRole.user_id == user_id).first()
    if not active or not active.role_id:
        raise APIError("ROLE_NOT_SELECTED", "Select a role first", 400)
    plan = db.query(Plan).filter(Plan.user_id == user_id, Plan.role_id == active.role_id).first()
    if not plan:
        raise APIError("PLAN_NOT_FOUND", "No plan for this role", 404)
    plan.status = data.status
    db.commit()
    return {"ok": True}


@router.get("/current")
def plan_current(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    active = db.query(UserActiveRole).filter(UserActiveRole.user_id == user_id).first()
    if not active or not active.role_id:
        return None
    plan = db.query(Plan).filter(Plan.user_id == user_id, Plan.role_id == active.role_id).first()
    if not plan:
        return None
    skills = db.query(PlanSkill).filter(PlanSkill.plan_id == plan.id).order_by(PlanSkill.position).all()
    from app.models import Skill
    out = {
        "id": plan.id,
        "deadline_date": plan.deadline_date.isoformat(),
        "hours_per_week": plan.hours_per_week,
        "status": plan.status,
        "skills": [{"skill_id": ps.skill_id, "name": db.query(Skill).filter(Skill.id == ps.skill_id).first().name if db.query(Skill).filter(Skill.id == ps.skill_id).first() else ""} for ps in skills],
    }
    return out
