"""Ollama/TinyLlama client for structured extraction. Timeouts and fallback on failure."""
import json
import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
RESUME_TIMEOUT = 8.0
JOB_TIMEOUT = 8.0
MAPPING_TIMEOUT = 5.0


def _post_generate(prompt: str, timeout: float, json_schema_hint: str = "") -> str | None:
    url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
    payload = {
        "model": "tinyllama",
        "prompt": prompt,
        "stream": False,
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
Schema:
{{ "skills": ["skill1", "skill2"], "degree": {{ "type": "string or null", "graduation_year": "string or null" }}, "experience": [ {{ "title": "string or null", "bullets": ["bullet1"] }} ] }}

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


def extract_job_structured(pdf_text: str) -> dict[str, Any] | None:
    """
    Extract job posting structure: title_original, role_canonical, degree_required,
    experience_required, what_you_will_do_excerpt, skills { required, preferred, description }.
    """
    prompt = f"""Extract from this job posting and return ONLY valid JSON (no markdown).
Schema:
{{ "title_original": "string", "role_canonical": "string", "degree_required": "string or null", "experience_required": "string or null", "what_you_will_do_excerpt": "string or null", "skills": {{ "required": [], "preferred": [], "description": [] }} }}

Posting text:
{pdf_text[:10000]}
"""
    response = _post_generate(prompt, JOB_TIMEOUT)
    if not response:
        return None
    text = response.strip()
    start = text.find("{")
    if start >= 0:
        end = text.rfind("}") + 1
        if end > start:
            try:
                data = json.loads(text[start:end])
                if "title_original" in data and "skills" in data:
                    return data
            except json.JSONDecodeError:
                pass
    return None


def propose_skill_mappings(skill_names: list[str]) -> dict[str, Any] | None:
    """Propose parent mappings: { "mappings": [ { "child": "...", "parent": "...", "category": "hard|soft|null" } ] }."""
    prompt = f"""For each skill, suggest a parent skill name if it fits under a broader category. Return ONLY valid JSON.
Schema: {{ "mappings": [ {{ "child": "skill name", "parent": "parent name or null", "category": "hard or soft or null" }} ] }}

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
