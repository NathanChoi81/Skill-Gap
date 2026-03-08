"""Ollama/TinyLlama client for structured extraction. Timeouts and fallback on failure."""
import json
import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
RESUME_TIMEOUT = 30.0
JOB_TIMEOUT = 60.0
COURSE_TIMEOUT = 45.0
MAPPING_TIMEOUT = 15.0


def _post_generate(prompt: str, timeout: float, json_schema_hint: str = "") -> str | None:
    url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
    payload = {
        "model": "tinyllama",
        "prompt": prompt,
        "stream": False,
        # Hint to Ollama that we want JSON output.
        "format": "json",
    }
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
            return data.get("response") or ""
    except Exception as e:
        logger.warning("Ollama call failed: %s", e)
        return None


def extract_resume_structured(raw_text: str) -> dict[str, Any] | None:
    """
    Call TinyLlama to extract skills, degree, experience from resume text.
    Returns dict with keys: skills (list[str]), degree (dict), experience (list).
    Returns None on timeout/invalid JSON → caller uses fallback.
    """
    prompt = f"""Extract from this resume text and return ONLY valid JSON (no markdown, no explanation).
Return a single JSON object with this exact shape (keys and types):
{{ "skills": ["Python", "FastAPI"], "degree": {{ "type": "string or null", "graduation_year": "string or null" }}, "experience": [ {{ "title": "string or null", "bullets": ["bullet1"] }} ] }}

Fill in realistic values based on the resume.

Resume text:
{raw_text[:8000]}
"""
    response = _post_generate(prompt, RESUME_TIMEOUT)
    if not response:
        return None
    # Try to find JSON in response
    text = response.strip()
    start = text.find("{")
    if start >= 0:
        end = text.rfind("}") + 1
        if end > start:
            try:
                data = json.loads(text[start:end])
                if "skills" in data and isinstance(data["skills"], list):
                    return {
                        "skills": data["skills"],
                        "degree": data.get("degree") or {"type": None, "graduation_year": None},
                        "experience": data.get("experience") or [],
                    }
            except json.JSONDecodeError:
                pass
    return None


def extract_course_structured(pdf_text: str) -> dict[str, Any] | None:
    """
    Extract course/learning resource structure from PDF text.
    Returns dict with: title, skill_name (to map to skill_id), difficulty (1-5),
    duration_hours, format (e.g. video, reading), url (optional).
    """
    prompt = f"""Extract from this course or learning resource and return ONLY valid JSON (no markdown).
Return a single JSON object with this exact shape:
{{ "title": "string", "skill_name": "string", "difficulty": 1-5, "duration_hours": number, "format": "video" or "reading" or "interactive", "url": "string or null" }}

Guidelines:
- title: course or resource title.
- skill_name: the primary skill/topic (e.g. Docker, Redis, Microservices, Python).
- difficulty: integer 1 (beginner) to 5 (advanced).
- duration_hours: estimated hours to complete (number).
- format: video, reading, or interactive.
- url: link if mentioned, else null.

Content:
{pdf_text[:8000]}
"""
    response = _post_generate(prompt, COURSE_TIMEOUT)
    if not response:
        return None
    text = response.strip()
    start = text.find("{")
    if start < 0:
        return None
    end = text.rfind("}") + 1
    if end <= start:
        return None
    try:
        data = json.loads(text[start:end])
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    title = data.get("title") or data.get("name") or ""
    skill_name = data.get("skill_name") or data.get("skill") or data.get("topic") or ""
    difficulty = data.get("difficulty")
    if difficulty is None or not isinstance(difficulty, (int, float)):
        difficulty = 3
    difficulty = max(1, min(5, int(difficulty)))
    duration = data.get("duration_hours") or data.get("duration_hours")
    if duration is None or not isinstance(duration, (int, float)):
        duration = 1.0
    duration = max(0.1, float(duration))
    format_ = data.get("format") or "reading"
    if not isinstance(format_, str):
        format_ = "reading"
    url = data.get("url") if isinstance(data.get("url"), str) else None
    return {
        "title": title.strip() or "Untitled",
        "skill_name": skill_name.strip() if skill_name else "",
        "difficulty": difficulty,
        "duration_hours": round(duration, 1),
        "format": format_.lower()[:100],
        "url": url,
    }


def extract_job_structured(pdf_text: str, debug: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """
    Extract job posting structure: title_original, role_canonical, degree_required,
    experience_required, what_you_will_do_excerpt, skills { required, preferred, description }.
    """
    prompt = f"""Extract from this job posting and return ONLY valid JSON (no markdown).
Return a single JSON object with this exact shape (keys and types):
{{ "title_original": "string", "role_canonical": "string", "degree_required": "string or null", "experience_required": "string or null", "what_you_will_do_excerpt": "string or null", "skills": {{ "required": ["Python", "FastAPI"], "preferred": ["Docker"], "description": ["data pipelines", "microservices"] }} }}

Guidelines:
- Use the job posting text to fill in realistic values.
- Do NOT output the literal words "string" or "string or null" anywhere in the JSON values.
- The example skill values ("Python", "FastAPI", "Docker", "data pipelines", "microservices") are just examples; replace them with skills actually mentioned in the posting.
- Populate skills.required with concrete required skills (languages, frameworks, tools) explicitly called out as requirements, must-haves, or core responsibilities.
- Populate skills.preferred with skills that are nice-to-have, bonuses, or listed under preferred qualifications.
- Populate skills.description with broader themes or abilities inferred from the responsibilities (e.g., "microservices", "data pipelines").

Posting text:
{pdf_text[:10000]}
"""
    response = _post_generate(prompt, JOB_TIMEOUT)
    if not response:
        # If the model call failed or timed out, fall back to a purely
        # heuristic extraction so callers can still treat this as an
        # "ai-derived" job instead of using the legacy fallback path.
        lines = [ln.strip() for ln in (pdf_text or "").splitlines() if ln.strip()]
        title = lines[0] if lines else ""
        excerpt = (pdf_text or "")[:500] if pdf_text else None
        return {
            "title_original": title,
            "role_canonical": title or "Unknown",
            "degree_required": None,
            "experience_required": None,
            "what_you_will_do_excerpt": excerpt,
            "skills": {"required": [], "preferred": [], "description": []},
        }
    text = response.strip()
    start = text.find("{")
    if start >= 0:
        end = text.rfind("}") + 1
        if end > start:
            try:
                raw_obj = json.loads(text[start:end])
            except json.JSONDecodeError as e:
                # If JSON is slightly malformed, fall back to a minimal heuristic
                # extraction rather than giving up entirely.
                logger.warning(
                    "Failed to decode job JSON from TinyLlama: %s; raw response (truncated)=%r",
                    e,
                    text[:300],
                )
                raw_obj = {}

            if not isinstance(raw_obj, dict):
                raw_obj = {}

            def _normalize_placeholder(value: Any) -> Any:
                if isinstance(value, str) and value.strip().lower() in {
                    "string",
                    "string or null",
                }:
                    return None
                return value

            # Derive a reasonable title from either the model output or the PDF text itself.
            model_title = (
                raw_obj.get("title_original")
                or raw_obj.get("job_title")
                or raw_obj.get("title")
            )
            if isinstance(model_title, str) and model_title.strip().lower() not in {
                "string",
                "string or null",
            }:
                title = model_title.strip()
            else:
                # Heuristic: first non-empty line from the PDF text.
                first_line = ""
                for line in (pdf_text or "").splitlines():
                    line = line.strip()
                    if line:
                        first_line = line
                        break
                title = first_line or None

            # Normalize common misspellings / variations from TinyLlama for role.
            role = (
                raw_obj.get("role_canonical")
                or raw_obj.get("role_canonicaal")
                or raw_obj.get("role")
                or title
            )
            degree_required = (
                _normalize_placeholder(
                    raw_obj.get("degree_required")
                    or raw_obj.get("degree")
                    or raw_obj.get("education")
                )
            )
            experience_required = (
                _normalize_placeholder(
                    raw_obj.get("experience_required")
                    or raw_obj.get("experiencce_required")
                    or raw_obj.get("experience")
                )
            )
            excerpt = (
                _normalize_placeholder(
                    raw_obj.get("what_you_will_do_excerpt")
                    or raw_obj.get("what_you_will_do")
                    or raw_obj.get("summary")
                )
            )

            skills = raw_obj.get("skills")
            if not isinstance(skills, dict):
                skills = {"required": [], "preferred": [], "description": []}
            else:
                description_raw = list(skills.get("description") or [])
                # Some model responses have a misspelled "descripion" field.
                description_raw += list(skills.get("descripion") or [])
                skills = {
                    "required": [
                        s for s in (skills.get("required") or []) if isinstance(s, str)
                    ],
                    "preferred": [
                        s
                        for s in (skills.get("preferred") or [])
                        if isinstance(s, str)
                    ],
                    "description": [s for s in description_raw if isinstance(s, str)],
                }

            return {
                "title_original": title or "",
                "role_canonical": role or "Unknown",
                "degree_required": degree_required,
                "experience_required": experience_required,
                "what_you_will_do_excerpt": excerpt,
                "skills": skills,
            }
    # Response had no parseable JSON block; use heuristic so we never return None.
    lines = [ln.strip() for ln in (pdf_text or "").splitlines() if ln.strip()]
    title = lines[0] if lines else ""
    excerpt = (pdf_text or "")[:500] if pdf_text else None
    return {
        "title_original": title,
        "role_canonical": title or "Unknown",
        "degree_required": None,
        "experience_required": None,
        "what_you_will_do_excerpt": excerpt,
        "skills": {"required": [], "preferred": [], "description": []},
    }


def propose_skill_mappings(skill_names: list[str]) -> dict[str, Any] | None:
    """Propose parent mappings: { "mappings": [ { "child": "...", "parent": "...", "category": "hard|soft|null" } ] }."""
    prompt = f"""For each skill, suggest a parent skill name if it fits under a broader category. Return ONLY valid JSON.
Return a single JSON object with this exact shape (keys and types):
{{ "mappings": [ {{ "child": "skill name", "parent": "parent name or null", "category": "hard or soft or null" }} ] }}

Fill in realistic values based on the skills list.

Skills: {json.dumps(skill_names)}
"""
    response = _post_generate(prompt, MAPPING_TIMEOUT)
    if not response:
        return None
    text = response.strip()
    start = text.find("{")
    if start >= 0:
        end = text.rfind("}") + 1
        if end > start:
            try:
                data = json.loads(text[start:end])
                if "mappings" in data:
                    return data
            except json.JSONDecodeError:
                pass
    return None
