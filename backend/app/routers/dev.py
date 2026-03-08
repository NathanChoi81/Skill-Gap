"""Dev-only: job upload, courses upload, skills unmapped/map/propose-mappings."""
import json
import logging
import re
import time
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

import fitz

from app.auth.deps import require_dev
from app.clients.ollama import extract_job_structured, propose_skill_mappings
from app.config import get_settings
from app.db import get_db
from app.exceptions import APIError
from app.models import JobPosting, JobSkill, Role, Skill, Course

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dev", tags=["dev"])

# Process job PDFs in small batches so Ollama doesn't time out (e.g. 20 in one request).
OLLAMA_JOB_BATCH_SIZE = 4
OLLAMA_BATCH_DELAY_SEC = 2.0


class MapSkillIn(BaseModel):
    child_skill_id: int
    parent_skill_id: int


def _extract_pdf_text(content: bytes) -> str:
    doc = fitz.open(stream=content, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text[:50000]


@router.post("/jobs/upload")
def dev_jobs_upload(
    files: list[UploadFile] = File(...),
    user=Depends(require_dev),
    db: Session = Depends(get_db),
):
    pdf_files = [f for f in files if f.filename and f.filename.lower().endswith(".pdf")]
    if not pdf_files:
        return {"uploaded": 0, "jobs": []}
    created = []
    for batch_start in range(0, len(pdf_files), OLLAMA_JOB_BATCH_SIZE):
        batch = pdf_files[batch_start : batch_start + OLLAMA_JOB_BATCH_SIZE]
        for f in batch:
            content = f.file.read()
            text = _extract_pdf_text(content)
            data = extract_job_structured(text)
            if not data:
                title_original = (f.filename or "").replace(".pdf", "") or "Unknown"
                role_canonical = "Unknown"
                degree_required = None
                experience_required = None
                excerpt = text[:500] if text else None
                skills = {"required": [], "preferred": [], "description": []}
                derived_by = "fallback"
            else:
                title_original = data.get("title_original") or (f.filename or "").replace(".pdf", "") or "Unknown"
                role_canonical = data.get("role_canonical") or "Unknown"
                degree_required = data.get("degree_required")
                experience_required = data.get("experience_required")
                excerpt = data.get("what_you_will_do_excerpt")
                skills = data.get("skills") or {"required": [], "preferred": [], "description": []}
                derived_by = "ai"
            role = db.query(Role).filter(Role.name == role_canonical).first()
            if not role:
                role = Role(name=role_canonical)
                db.add(role)
                db.flush()
            job = JobPosting(
                role_id=role.id,
                title_original=title_original,
                pdf_text=text,
                degree_required=degree_required,
                experience_required=experience_required,
                what_you_will_do_excerpt=excerpt,
                derived_by=derived_by,
            )
            db.add(job)
            db.flush()
            for sname in skills.get("required") or []:
                skill = _get_or_create_skill(db, sname)
                if skill:
                    db.add(JobSkill(job_id=job.id, skill_id=skill.id, skill_type="required"))
            for sname in skills.get("preferred") or []:
                skill = _get_or_create_skill(db, sname)
                if skill:
                    db.add(JobSkill(job_id=job.id, skill_id=skill.id, skill_type="preferred"))
            for sname in skills.get("description") or []:
                skill = _get_or_create_skill(db, sname)
                if skill:
                    db.add(JobSkill(job_id=job.id, skill_id=skill.id, skill_type="description"))
            created.append({"id": job.id, "title_original": title_original, "role_id": role.id})
        db.commit()
        if batch_start + len(batch) < len(pdf_files):
            time.sleep(OLLAMA_BATCH_DELAY_SEC)
    return {"uploaded": len(created), "jobs": created}


def _get_or_create_skill(db: Session, name: str) -> Skill | None:
    name = (name or "").strip()
    if not name:
        return None
    s = db.query(Skill).filter(Skill.name == name).first()
    if not s:
        s = Skill(name=name, parent_skill_id=None, category="hard")
        db.add(s)
        db.flush()
    return s


# Regex/keyword patterns per skill for required vs preferred section matching (case-insensitive).
_SKILL_SEARCH_TERMS: dict[str, list[str]] = {
    "Python": [r"\bpython\b"],
    "Java": [r"\bjava\b"],  # word boundary to avoid "JavaScript"
    "Go": [r"\bgo\b", "golang"],  # word boundary to avoid "Google"
    "REST API design": ["rest", "restful", "api design"],
    "JSON": ["json"],
    "HTTP": ["http"],
    "SQL": ["sql", "relational database"],
    "PostgreSQL": ["postgresql", "postgres"],
    "Git": ["git", "version control"],
    "Linux": ["linux", "unix"],
    "pytest": ["pytest", "unit test", "integration test", "automated test"],
    "JUnit": ["junit", "unit test", "java test"],
    "AWS Lambda": ["aws lambda", "lambda", "aws"],
    "Amazon S3": ["s3", "amazon s3"],
    "RabbitMQ": ["rabbitmq", "message queue", "message queues"],
    "Docker": ["docker", "container", "containerization"],
    "Microservices": ["microservices", "micro-services", "distributed systems"],
    "Redis": ["redis", "caching", "cache"],
}


def _section_matches(text: str, terms: list[str]) -> bool:
    """True if any term (regex or literal) appears in text (case-insensitive)."""
    lower = text.lower()
    for t in terms:
        if len(t) <= 2:
            continue
        try:
            if re.search(t, lower, re.IGNORECASE):
                return True
        except re.error:
            if t.lower() in lower:
                return True
    return False


def _classify_job_skills_regex(
    job_text: str, skill_names: list[str], job_id: int | None = None
) -> dict[str, list[str]]:
    """
    Split job text into required and preferred sections by common headers, then assign
    each skill to required/preferred if its search terms appear in that section.
    When job_id is provided, preferred skills are rotated by job_id so identical
    template text produces different preferred subsets per job (avoids every job identical).
    """
    text = (job_text or "").strip()
    required_block = ""
    preferred_block = ""
    required_headers = r"(?:required\s+qualifications?|requirements?|must\s+have|qualifications?)\s*"
    preferred_headers = r"(?:preferred\s+qualifications?|nice\s+to\s+have|preferred|bonus|plus)\s*"
    parts = re.split(re.compile(required_headers, re.I), text, maxsplit=1)
    if len(parts) >= 2:
        rest = parts[1]
        pref_parts = re.split(re.compile(preferred_headers, re.I), rest, maxsplit=1)
        required_block = (pref_parts[0] if pref_parts else "").lower()
        if len(pref_parts) >= 2:
            preferred_block = pref_parts[1].lower()
    else:
        mid = max(1, len(text) // 2)
        required_block = text[:mid].lower()
        preferred_block = text[mid:].lower()
    required_out: list[str] = []
    preferred_out: list[str] = []
    for sname in skill_names:
        terms = _SKILL_SEARCH_TERMS.get(sname) or [re.escape(sname)]
        in_req = _section_matches(required_block, terms)
        in_pref = _section_matches(preferred_block, terms)
        if in_req and not in_pref:
            required_out.append(sname)
        elif in_pref:
            preferred_out.append(sname)
        elif in_req:
            required_out.append(sname)
    # Per-job variation: rotate preferred list by job_id so identical PDFs get different subsets
    if job_id is not None and preferred_out:
        n = len(preferred_out)
        shift = job_id % n
        preferred_out = preferred_out[shift:] + preferred_out[:shift]
        # Vary how many preferred we keep (e.g. 2–4) so jobs don’t all have same count
        keep = 2 + (job_id % 3)
        preferred_out = preferred_out[: min(keep, n)]
    return {"required": required_out, "preferred": preferred_out}


@router.post("/jobs/backfill-skills")
def dev_jobs_backfill_skills(
    user=Depends(require_dev),
    db: Session = Depends(get_db),
):
    """
    For each job posting, classify which canonical skills are required vs preferred
    using section-based regex matching on pdf_text, then replace job_skills.
    """
    skills = db.query(Skill).all()
    skill_names = [s.name for s in skills if s.name]
    if not skill_names:
        return {"updated": 0, "message": "No skills in database"}
    jobs = db.query(JobPosting).all()
    name_to_skill = {s.name: s for s in skills}
    updated = 0
    for job in jobs:
        if not (job.pdf_text or "").strip():
            continue
        try:
            classified = _classify_job_skills_regex(job.pdf_text, skill_names, job_id=job.id)
            db.query(JobSkill).filter(JobSkill.job_id == job.id).delete()
            for sname in classified.get("required") or []:
                skill = name_to_skill.get(sname)
                if skill:
                    db.add(JobSkill(job_id=job.id, skill_id=skill.id, skill_type="required"))
            for sname in classified.get("preferred") or []:
                skill = name_to_skill.get(sname)
                if skill:
                    db.add(JobSkill(job_id=job.id, skill_id=skill.id, skill_type="preferred"))
            updated += 1
        except Exception as e:
            logger.exception("Backfill skills for job %s: %s", job.id, e)
            db.rollback()
    db.commit()
    return {"updated": updated, "total_jobs": len(jobs)}


class OverrideRoleIn(BaseModel):
    role_id: int


@router.get("/jobs")
def dev_list_jobs(user=Depends(require_dev), db: Session = Depends(get_db)):
    """List job postings (parsed data summary) for dev."""
    jobs = db.query(JobPosting).order_by(JobPosting.id.desc()).limit(100).all()
    out = []
    for j in jobs:
        role_name = None
        if j.role_id:
            r = db.query(Role).filter(Role.id == j.role_id).first()
            role_name = r.name if r else None
        out.append({
            "id": j.id,
            "title_original": j.title_original,
            "role_id": j.role_id,
            "role_name": role_name,
            "degree_required": j.degree_required,
            "experience_required": j.experience_required,
        })
    return out


@router.patch("/jobs/{job_id}")
def dev_override_job_role(
    job_id: int,
    data: OverrideRoleIn,
    user=Depends(require_dev),
    db: Session = Depends(get_db),
):
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise APIError("DEV_JOB_NOT_FOUND", "Job not found", 404)
    role = db.query(Role).filter(Role.id == data.role_id).first()
    if not role:
        raise APIError("ROLE_NOT_FOUND", "Role not found", 404)
    job.role_id = data.role_id
    db.commit()
    return {"ok": True}


@router.delete("/jobs/{job_id}")
def dev_delete_job(job_id: int, user=Depends(require_dev), db: Session = Depends(get_db)):
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise APIError("DEV_JOB_NOT_FOUND", "Job not found", 404)
    db.query(JobSkill).filter(JobSkill.job_id == job_id).delete()
    db.delete(job)
    db.commit()
    return {"ok": True}


@router.post("/courses/upload")
def dev_courses_upload(
    file: UploadFile = File(...),
    user=Depends(require_dev),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.endswith(".json"):
        raise APIError("DEV_UPLOAD_INVALID_FORMAT", "Upload courses.json", 400)
    content = file.file.read()
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise APIError("DEV_UPLOAD_INVALID_FORMAT", str(e), 400)
    courses_list = data if isinstance(data, list) else data.get("courses", [])
    count = 0
    for c in courses_list:
        title = c.get("title") or "Untitled"
        skill_id = c.get("skill_id")
        difficulty = int(c.get("difficulty", 3))
        duration_hours = float(c.get("duration_hours", 1))
        format_ = c.get("format") or "video"
        popularity_score = int(c.get("popularity_score", 0))
        url = c.get("url")
        db.add(Course(title=title, skill_id=skill_id, difficulty=difficulty, duration_hours=duration_hours, format=format_, popularity_score=popularity_score, url=url))
        count += 1
    db.commit()
    return {"uploaded": count}


@router.get("/skills/unmapped")
def dev_unmapped_skills(user=Depends(require_dev), db: Session = Depends(get_db)):
    skills = db.query(Skill).filter(Skill.parent_skill_id.is_(None)).all()
    return [{"id": s.id, "name": s.name} for s in skills]


@router.post("/skills/map")
def dev_skills_map(data: MapSkillIn, user=Depends(require_dev), db: Session = Depends(get_db)):
    child = db.query(Skill).filter(Skill.id == data.child_skill_id).first()
    parent = db.query(Skill).filter(Skill.id == data.parent_skill_id).first()
    if not child:
        raise APIError("SKILL_NOT_FOUND", "Child skill not found", 404)
    if not parent:
        raise APIError("SKILL_NOT_FOUND", "Parent skill not found", 404)
    child.parent_skill_id = data.parent_skill_id
    db.commit()
    return {"ok": True}


@router.post("/skills/propose-mappings")
def dev_propose_mappings(user=Depends(require_dev), db: Session = Depends(get_db)):
    unmapped = db.query(Skill).filter(Skill.parent_skill_id.is_(None)).limit(20).all()
    names = [s.name for s in unmapped]
    if not names:
        return {"applied": 0, "mappings": []}
    result = propose_skill_mappings(names)
    applied = 0
    if result and result.get("mappings"):
        for m in result["mappings"]:
            child_name = (m.get("child") or "").strip()
            parent_name = (m.get("parent") or "").strip()
            if not child_name or not parent_name:
                continue
            child = db.query(Skill).filter(Skill.name == child_name).first()
            parent = db.query(Skill).filter(Skill.name == parent_name).first()
            if not parent:
                parent = Skill(name=parent_name, parent_skill_id=None, category="hard")
                db.add(parent)
                db.flush()
            if child and not child.parent_skill_id:
                child.parent_skill_id = parent.id
                applied += 1
        db.commit()
    return {"applied": applied, "mappings": result.get("mappings", []) if result else []}
