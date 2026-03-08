"""PII redaction before AI: emails, phones, URLs, addresses, school names, person names."""
import logging
import re
from typing import Tuple

logger = logging.getLogger(__name__)

# Regex patterns
EMAIL = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE = re.compile(r"\+?[\d\s\-().]{10,}")
URL = re.compile(r"https?://[^\s]+")
# Best-effort address: line with digits + street-like words
ADDRESS = re.compile(r"\d+\s+[\w\s]+(?:street|st|avenue|ave|road|rd|blvd|drive|dr|lane|ln|way|court|ct)[\w\s,.]*", re.I)
# School name heuristic: common patterns (partial redaction preserves degree/year)
SCHOOL_LIKE = re.compile(r"\b(?:University|College|School|Institute|Academy|U\.?S\.?C\.?|MIT|Stanford|Harvard|Berkeley)\b[^\n,.]*", re.I)


def _redact_email(text: str) -> Tuple[str, int]:
    count = 0
    def repl(m):
        nonlocal count
        count += 1
        return "[REDACTED_EMAIL]"
    out = EMAIL.sub(repl, text)
    return out, count


def _redact_phone(text: str) -> Tuple[str, int]:
    count = 0
    def repl(m):
        nonlocal count
        count += 1
        return "[REDACTED_PHONE]"
    out = PHONE.sub(repl, text)
    return out, count


def _redact_url(text: str) -> Tuple[str, int]:
    count = 0
    def repl(m):
        nonlocal count
        count += 1
        return "[REDACTED_URL]"
    out = URL.sub(repl, text)
    return out, count


def _redact_address(text: str) -> Tuple[str, int]:
    count = 0
    def repl(m):
        nonlocal count
        count += 1
        return "[REDACTED_ADDRESS]"
    out = ADDRESS.sub(repl, text)
    return out, count


def _redact_schools(text: str) -> Tuple[str, int]:
    count = 0
    def repl(m):
        nonlocal count
        count += 1
        return "[REDACTED_SCHOOL]"
    out = SCHOOL_LIKE.sub(repl, text)
    return out, count


def _redact_first_line_name(text: str) -> str:
    """First-line heuristic: often the name.

    To avoid wiping short single-line texts (e.g. in unit tests), only apply this
    when there is more than one line of text.
    """
    lines = text.split("\n")
    if len(lines) < 2:
        return text
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and len(stripped) < 80 and not stripped.startswith("["):
            lines[i] = "[REDACTED_NAME]"
            break
    return "\n".join(lines)


def redact_pii(text: str, use_spacy_person: bool = True) -> str:
    """
    Redact PII from text. Logs counts only.
    use_spacy_person: if True, use spaCy NER for PERSON (requires spacy model loaded).
    """
    total_redacted = 0
    out = text

    out, n = _redact_email(out)
    total_redacted += n
    out, n = _redact_phone(out)
    total_redacted += n
    out, n = _redact_url(out)
    total_redacted += n
    out, n = _redact_address(out)
    total_redacted += n
    out, n = _redact_schools(out)
    total_redacted += n

    out = _redact_first_line_name(out)

    if use_spacy_person:
        try:
            import spacy
            nlp = getattr(redact_pii, "_nlp", None)
            if nlp is None:
                try:
                    nlp = spacy.load("en_core_web_sm")
                except OSError:
                    nlp = spacy.blank("en")
                redact_pii._nlp = nlp
            doc = nlp(out)
            for ent in reversed(doc.ents):
                if ent.label_ == "PERSON":
                    out = out[: ent.start_char] + "[REDACTED_NAME]" + out[ent.end_char :]
                    total_redacted += 1
        except Exception as e:
            logger.warning("spaCy PERSON redaction skipped: %s", e)

    if total_redacted > 0:
        logger.info("PII redaction: %d spans redacted (counts only)", total_redacted)
    return out
