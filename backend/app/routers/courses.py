"""Courses: list by skill (with adjusted difficulty), set status (branch completion rule)."""
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user_id
from app.db import get_db
from app.exceptions import APIError
from app.models import Course, UserCourseProgress, UserCourseMeta, UserSkill, Skill

router = APIRouter(tags=["courses"])


class StatusIn(BaseModel):
    status: str  # in_progress | complete


@router.get("/skills/{skill_id}/courses")
def list_courses(
    skill_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    courses = db.query(Course).filter(Course.skill_id == skill_id).order_by(Course.popularity_score.desc()).all()
    out = []
    for c in courses:
        meta = db.query(UserCourseMeta).filter(UserCourseMeta.user_id == user_id, UserCourseMeta.course_id == c.id).first()
        difficulty = meta.adjusted_difficulty if meta else c.difficulty
        prog = db.query(UserCourseProgress).filter(UserCourseProgress.user_id == user_id, UserCourseProgress.course_id == c.id).first()
        status = prog.status if prog else None
        out.append({
            "id": c.id,
            "title": c.title,
            "difficulty": difficulty,
            "duration_hours": c.duration_hours,
            "format": c.format,
            "popularity_score": c.popularity_score,
            "url": c.url,
            "status": status,
        })
    return out


@router.post("/courses/{course_id}/status")
def set_course_status(
    course_id: int,
    data: StatusIn,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if data.status not in ("in_progress", "complete"):
        raise APIError("COURSE_STATUS_INVALID", "status must be in_progress or complete", 400)
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise APIError("COURSE_NOT_FOUND", "Course not found", 404)
    skill_id = course.skill_id
    prog = db.query(UserCourseProgress).filter(UserCourseProgress.user_id == user_id, UserCourseProgress.course_id == course_id).first()
    if prog:
        prog.status = data.status
        prog.updated_at = datetime.utcnow()
    else:
        db.add(UserCourseProgress(user_id=user_id, course_id=course_id, status=data.status))
    db.commit()
    # Branch rule: when unfinished resources for this skill reach 0, auto-add skill
    if data.status == "complete":
        _maybe_auto_add_skill(db, user_id, skill_id)
    return {"ok": True}


def _maybe_auto_add_skill(db: Session, user_id: int, skill_id: int) -> None:
    """If user has no unfinished resources for this skill, add skill as 'course' (branch completion)."""
    if not skill_id:
        return
    courses_for_skill = db.query(Course).filter(Course.skill_id == skill_id).all()
    unfinished = 0
    for c in courses_for_skill:
        prog = db.query(UserCourseProgress).filter(UserCourseProgress.user_id == user_id, UserCourseProgress.course_id == c.id).first()
        if not prog or prog.status != "complete":
            unfinished += 1
    if unfinished == 0:
        existing = db.query(UserSkill).filter(UserSkill.user_id == user_id, UserSkill.skill_id == skill_id).first()
        if not existing:
            db.add(UserSkill(user_id=user_id, skill_id=skill_id, source="course"))
            db.commit()
