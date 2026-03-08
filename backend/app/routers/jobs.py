"""Jobs: list by role with filters, job detail."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user_id
from app.db import get_db
from app.exceptions import APIError
from app.models import JobPosting, JobSkill, UserSkill, Skill, UserNotInterestedSkill
from app.services.role_analysis import get_or_compute_aggregates

router = APIRouter(tags=["jobs"])


def _user_skill_ids(db: Session, user_id: int) -> set:
    ids = set()
    for us in db.query(UserSkill).filter(UserSkill.user_id == user_id).all():
        ids.add(us.skill_id)
        s = db.query(Skill).filter(Skill.id == us.skill_id).first()
        if s and s.parent_skill_id:
            ids.add(s.parent_skill_id)
    return ids


def _job_match_score(db: Session, user_id: int, job_id: int) -> tuple[int, list[int], str]:
    """Returns (internal_score, missing_skill_ids, label)."""
    user_skills = _user_skill_ids(db, user_id)
    rows = db.query(JobSkill).filter(JobSkill.job_id == job_id).all()
    req, pref, desc = set(), set(), set()
    for r in rows:
        if r.skill_type == "required":
            req.add(r.skill_id)
        elif r.skill_type == "preferred":
            pref.add(r.skill_id)
        else:
            desc.add(r.skill_id)
    req_cov = len(req & user_skills) / len(req) if req else 1.0
    pref_cov = len(pref & user_skills) / len(pref) if pref else 1.0
    desc_cov = len(desc & user_skills) / len(desc) if desc else 1.0
    score = round(100 * (0.60 * req_cov + 0.25 * pref_cov + 0.15 * desc_cov))
    if score < 50:
        label = "Developing"
    elif score < 80:
        label = "Competitive"
    else:
        label = "Ready"
    missing = (req | pref | desc) - user_skills
    return score, list(missing), label


@router.get("/roles/{role_id}/jobs")
def list_jobs(
    role_id: int,
    sort: str = Query("score"),
    degree: str | None = None,
    experience: str | None = None,
    desc_match: int | None = None,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    jobs = db.query(JobPosting).filter(JobPosting.role_id == role_id).all()
    out = []
    for job in jobs:
        score, missing_ids, label = _job_match_score(db, user_id, job.id)
        missing_names = [db.query(Skill).filter(Skill.id == sid).first().name for sid in missing_ids]
        missing_names = [n for n in missing_names if n]
        out.append({
            "id": job.id,
            "title_original": job.title_original,
            "label": label,
            "internal_score": score,
            "missing_skills": missing_names,
            "missing_skill_ids": missing_ids,
        })
    if sort == "score":
        out.sort(key=lambda x: -x["internal_score"])
    return out


@router.get("/jobs/{job_id}")
def job_detail(job_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise APIError("JOB_NOT_FOUND", "Job not found", 404)
    score, missing_ids, label = _job_match_score(db, user_id, job.id)
    missing_names = [db.query(Skill).filter(Skill.id == sid).first().name for sid in missing_ids]
    missing_names = [n for n in missing_names if n]
    rows = db.query(JobSkill, Skill).join(Skill, JobSkill.skill_id == Skill.id).filter(JobSkill.job_id == job_id).all()
    required = [s.name for js, s in rows if js.skill_type == "required"]
    preferred = [s.name for js, s in rows if js.skill_type == "preferred"]
    description = [s.name for js, s in rows if js.skill_type == "description"]
    return {
        "id": job.id,
        "title_original": job.title_original,
        "what_you_will_do_excerpt": job.what_you_will_do_excerpt or "",
        "label": label,
        "required": required,
        "preferred": preferred,
        "description": description,
        "missing_skills": missing_names,
    }
