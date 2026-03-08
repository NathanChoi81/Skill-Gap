"""Plan generation: greedy fit by priority into budget_hours."""
import json
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models import RoleAggregate, UserNotInterestedSkill, Course, UserSkill, Skill

TYPE_WEIGHTS = {"required": 1.0, "preferred": 0.6, "description": 0.3}


def get_gaps_for_plan(db: Session, user_id: int, role_id: int) -> list[dict]:
    """Missing skills with frequency and type for role, excluding not-interested."""
    agg = db.query(RoleAggregate).filter(RoleAggregate.role_id == role_id).first()
    if not agg:
        return []
    try:
        data = json.loads(agg.aggregated_skill_frequency_json)
    except json.JSONDecodeError:
        return []
    user_skill_ids = set()
    for us in db.query(UserSkill).filter(UserSkill.user_id == user_id).all():
        user_skill_ids.add(us.skill_id)
        s = db.query(Skill).filter(Skill.id == us.skill_id).first()
        if s and s.parent_skill_id:
            user_skill_ids.add(s.parent_skill_id)
    not_interested = set(
        n.skill_id for n in db.query(UserNotInterestedSkill).filter(UserNotInterestedSkill.user_id == user_id).all()
    )
    missing_ids = set(item["skill_id"] for item in data.get("skills", [])) - user_skill_ids - not_interested
    out = []
    for item in data.get("skills", []):
        sid = item.get("skill_id")
        if sid not in missing_ids:
            continue
        req = item.get("required", 0)
        pref = item.get("preferred", 0)
        desc = item.get("description", 0)
        priority = req * TYPE_WEIGHTS["required"] + pref * TYPE_WEIGHTS["preferred"] + desc * TYPE_WEIGHTS["description"]
        hours = 0.0
        for c in db.query(Course).filter(Course.skill_id == sid).all():
            hours += c.duration_hours
        if hours == 0:
            hours = 5.0
        out.append({"skill_id": sid, "priority": priority, "hours": hours})
    return sorted(out, key=lambda x: -x["priority"])


def propose_plan(db: Session, user_id: int, role_id: int, deadline: date, hours_per_week: int) -> dict:
    """
    Returns { "skills": [ { "skill_id", "name", "estimated_hours", "priority" } ], "total_hours", "budget_hours", "warning" }.
    """
    gaps = get_gaps_for_plan(db, user_id, role_id)
    if not gaps:
        return {"skills": [], "total_hours": 0, "budget_hours": 0, "warning": "No gaps or role not analyzed."}
    today = date.today()
    if deadline <= today:
        return {"skills": [], "total_hours": 0, "budget_hours": 0, "warning": "Deadline must be in the future."}
    weeks = max(1, (deadline - today).days // 7)
    budget_hours = weeks * hours_per_week
    skill_names = {s.id: s.name for s in db.query(Skill).filter(Skill.id.in_([g["skill_id"] for g in gaps])).all()}
    fitted = []
    used = 0.0
    for g in gaps:
        if used + g["hours"] <= budget_hours:
            fitted.append({
                "skill_id": g["skill_id"],
                "name": skill_names.get(g["skill_id"], ""),
                "estimated_hours": g["hours"],
                "priority": g["priority"],
            })
            used += g["hours"]
        else:
            if not fitted:
                fitted.append({
                    "skill_id": g["skill_id"],
                    "name": skill_names.get(g["skill_id"], ""),
                    "estimated_hours": g["hours"],
                    "priority": g["priority"],
                })
                used += g["hours"]
            break
    warning = ""
    if fitted and used > budget_hours:
        warning = "Budget too small; top skill(s) still proposed."
    return {
        "skills": fitted,
        "total_hours": used,
        "budget_hours": budget_hours,
        "warning": warning,
    }
