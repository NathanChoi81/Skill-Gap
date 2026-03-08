"""Resume text extraction: PyMuPDF, PII redaction, AI or fallback skill extraction, encrypt store."""
import logging
import re
from typing import Any

import fitz  # PyMuPDF

from app.clients.ollama import extract_resume_structured
from app.services.redaction import redact_pii
from app.services.resume_encryption import encrypt_resume_text

logger = logging.getLogger(__name__)

# Fallback: simple skill-like phrases (words that look like tech/skills)
SKILL_WORDS = re.compile(r"\b([A-Z][a-z]*(?:\s+[A-Z][a-z]*)*)\b")
# Limit extracted text length
MAX_TEXT_LENGTH = 100_000


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH]
        logger.warning("Resume text truncated to %s chars", MAX_TEXT_LENGTH)
    return text


def extract_skills_fallback(text: str) -> list[str]:
    """Fallback: regex + simple word extraction. Returns list of candidate skill strings."""
    skills = set()
    # Look for comma/separator separated items that might be skills
    for part in re.split(r"[,;|\n]", text):
        part = part.strip()
        if 2 <= len(part) <= 50 and part not in ("and", "the", "with", "for", "etc"):
            skills.add(part)
    return list(skills)[:100]


def run_resume_pipeline(pdf_bytes: bytes, use_ai: bool) -> tuple[str, list[str], dict, list]:
    """
    Returns (redacted_text_plain, skills_list, degree_dict, experience_list).
    Redacted text is already encrypted for storage by caller.
    """
    raw = extract_text_from_pdf(pdf_bytes)
    redacted = redact_pii(raw)
    skills = []
    degree = {"type": None, "graduation_year": None}
    experience = []

    if use_ai:
        structured = extract_resume_structured(redacted)
        if structured:
            skills_raw = structured.get("skills")
            skills = [str(s).strip() for s in skills_raw] if isinstance(skills_raw, list) else []
            degree = structured.get("degree") or degree
            experience = structured.get("experience") or []
        else:
            skills = extract_skills_fallback(redacted)
    else:
        skills = extract_skills_fallback(redacted)

    return redacted, skills, degree, experience
