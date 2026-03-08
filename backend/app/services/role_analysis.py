"""Role aggregates: compute and cache required/preferred/description frequencies per role."""
import json
import logging
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models import JobPosting, JobSkill, Role, RoleAggregate, Skill

logger = logging.getLogger(__name__)

TYPE_WEIGHTS = {"required": 1.0, "preferred": 0.6, "description": 0.3}


def compute_role_aggregates(db: Session, role_id: int) -> dict:
    """Compute aggregated_skill_frequency_json for role from job_postings + job_skills."""
    jobs = db.query(JobPosting).filter(JobPosting.role_id == role_id).all()
    freq = defaultdict(lambda: {"required": 0, "preferred": 0, "description": 0})
    for job in jobs:
        for js in db.query(JobSkill).filter(JobSkill.job_id == job.id).all():
            key = str(js.skill_id)
            freq[key][js.skill_type] += 1
    # Normalize to list of { skill_id, required, preferred, description }
    out = [{"skill_id": int(k), **v} for k, v in freq.items()]
    return {"skills": out}


def get_or_compute_aggregates(db: Session, role_id: int, force_recompute: bool = False) -> dict:
    """Get stored aggregates or compute and store. If force_recompute=True, recompute from current job_skills."""
    if not force_recompute:
        agg = db.query(RoleAggregate).filter(RoleAggregate.role_id == role_id).first()
        if agg:
            try:
                return json.loads(agg.aggregated_skill_frequency_json)
            except json.JSONDecodeError:
                pass
    else:
        db.query(RoleAggregate).filter(RoleAggregate.role_id == role_id).delete()
        db.commit()
    data = compute_role_aggregates(db, role_id)
    from datetime import datetime
    row = db.query(RoleAggregate).filter(RoleAggregate.role_id == role_id).first()
    if row:
        row.aggregated_skill_frequency_json = json.dumps(data)
        row.computed_at = datetime.utcnow()
    else:
        db.add(RoleAggregate(role_id=role_id, aggregated_skill_frequency_json=json.dumps(data), computed_at=datetime.utcnow()))
    db.commit()
    return data


def compute_match_scores(db: Session, user_id: int, role_id: int) -> dict:
    """
    Returns required_match, preferred_match, description_match (0-100),
    internal_score (weighted), label (Developing/Competitive/Ready), missing_count, recommended_jobs.
    """
    from app.models import UserSkill, UserNotInterestedSkill, JobPosting, JobSkill
    aggregates = get_or_compute_aggregates(db, role_id)
    skill_list = aggregates.get("skills") or []
    if not skill_list:
        return {
            "required_match": 0,
            "preferred_match": 0,
            "description_match": 0,
            "internal_score": 0,
            "label": "Developing",
            "missing_count": 0,
            "recommended_jobs": 0,
        }
    # User's canonical skill ids (including from children via parent)
    user_skill_ids = set()
    for us in db.query(UserSkill).filter(UserSkill.user_id == user_id).all():
        user_skill_ids.add(us.skill_id)
        skill = db.query(Skill).filter(Skill.id == us.skill_id).first()
        if skill and skill.parent_skill_id:
            user_skill_ids.add(skill.parent_skill_id)
    not_interested = set(
        s.skill_id for s in db.query(UserNotInterestedSkill).filter(UserNotInterestedSkill.user_id == user_id).all()
    )
    # Required / preferred / description sets for role
    req_ids = set()
    pref_ids = set()
    desc_ids = set()
    for item in skill_list:
        sid = item.get("skill_id")
        if item.get("required", 0) > 0:
            req_ids.add(sid)
        if item.get("preferred", 0) > 0:
            pref_ids.add(sid)
        if item.get("description", 0) > 0:
            desc_ids.add(sid)
    req_cov = len(req_ids & user_skill_ids) / len(req_ids) if req_ids else 1.0
    pref_cov = len(pref_ids & user_skill_ids) / len(pref_ids) if pref_ids else 1.0
    desc_cov = len(desc_ids & user_skill_ids) / len(desc_ids) if desc_ids else 1.0
    required_match = round(100 * req_cov)
    preferred_match = round(100 * pref_cov)
    description_match = round(100 * desc_cov)
    internal_score = round(100 * (0.60 * req_cov + 0.25 * pref_cov + 0.15 * desc_cov))
    if internal_score < 50:
        label = "Developing"
    elif internal_score < 80:
        label = "Competitive"
    else:
        label = "Ready"
    missing = (req_ids | pref_ids | desc_ids) - user_skill_ids - not_interested
    missing_count = len(missing)
    jobs = db.query(JobPosting).filter(JobPosting.role_id == role_id).count()
    return {
        "required_match": required_match,
        "preferred_match": preferred_match,
        "description_match": description_match,
        "internal_score": internal_score,
        "label": label,
        "missing_count": missing_count,
        "recommended_jobs": jobs,
    }
