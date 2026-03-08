"""Resume upload and delete. Hard delete previous resume, purge resume-sourced skills."""
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user_id
from app.db import get_db
from app.exceptions import APIError
from app.models import Resume, UserSkill, Skill
from app.services.resume_encryption import encrypt_resume_text
from app.services.resume_extraction import run_resume_pipeline
from app.config import get_settings

router = APIRouter(prefix="/resumes", tags=["resumes"])
settings = get_settings()
MAX_BYTES = settings.max_resume_mb * 1024 * 1024


class UploadOut(BaseModel):
    resume_id: int
    extracted_skills: list[dict]
    mapped_skills: list[dict]


def _get_or_create_skill(db: Session, name: str) -> Skill:
    name = name.strip()
    if not name:
        return None
    skill = db.query(Skill).filter(Skill.name == name).first()
    if not skill:
        skill = Skill(name=name, parent_skill_id=None, category="hard")
        db.add(skill)
        db.flush()
    return skill


@router.post("/upload", response_model=UploadOut)
def upload_resume(
    file: UploadFile = File(...),
    use_ai: bool = Form(True),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise APIError("RESUME_INVALID_FILE_TYPE", "PDF only", 400)
    content = file.file.read()
    if len(content) > MAX_BYTES:
        raise APIError("RESUME_FILE_TOO_LARGE", f"File too large (max {settings.max_resume_mb} MB)", 400)

    # Hard delete previous resume and purge resume-sourced skills
    existing = db.query(Resume).filter(Resume.user_id == user_id).first()
    if existing:
        db.query(UserSkill).filter(UserSkill.user_id == user_id, UserSkill.source == "resume").delete()
        db.delete(existing)
        db.commit()

    try:
        redacted, skills_list, degree, experience = run_resume_pipeline(content, use_ai)
    except Exception as e:
        raise APIError("RESUME_EXTRACTION_FAILED", str(e), 500)

    encrypted = encrypt_resume_text(redacted)
    resume = Resume(user_id=user_id, encrypted_redacted_text=encrypted)
    db.add(resume)
    db.flush()

    extracted_skills = []
    source = "ai" if use_ai else "fallback"
    for name in skills_list:
        skill = _get_or_create_skill(db, name)
        if skill:
            if not db.query(UserSkill).filter(UserSkill.user_id == user_id, UserSkill.skill_id == skill.id).first():
                db.add(UserSkill(user_id=user_id, skill_id=skill.id, source="resume"))
            extracted_skills.append({"name": skill.name, "source": source})
    canon_to_children = {}
    for s in extracted_skills:
        skill = db.query(Skill).filter(Skill.name == s["name"]).first()
        if skill and skill.parent_skill_id:
            parent = db.query(Skill).filter(Skill.id == skill.parent_skill_id).first()
            if parent:
                canon_to_children.setdefault(parent.name, []).append(skill.name)
    mapped_skills = [{"canonical": c, "children": ch} for c, ch in canon_to_children.items()]

    db.commit()
    db.refresh(resume)
    return UploadOut(resume_id=resume.id, extracted_skills=extracted_skills, mapped_skills=mapped_skills)


@router.delete("/current")
def delete_current(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    existing = db.query(Resume).filter(Resume.user_id == user_id).first()
    if existing:
        db.query(UserSkill).filter(UserSkill.user_id == user_id, UserSkill.source == "resume").delete()
        db.delete(existing)
        db.commit()
    return {"ok": True}
