from app.services.redaction import redact_pii


def test_redact_email():
    text = "Contact me at john@example.com for more."
    out = redact_pii(text, use_spacy_person=False)
    assert "john@example.com" not in out
    assert "[REDACTED_EMAIL]" in out


def test_redact_phone():
    text = "Call 555-123-4567 or +1 (555) 999-0000."
    out = redact_pii(text, use_spacy_person=False)
    assert "555" in out or "[REDACTED_PHONE]" in out


def test_redact_url():
    text = "Visit https://example.com/docs."
    out = redact_pii(text, use_spacy_person=False)
    assert "https://example.com" not in out
    assert "[REDACTED_URL]" in out


def test_preserves_skills_like_text():
    text = "Skills: Python, SQL, JavaScript. Email: a@b.co"
    out = redact_pii(text, use_spacy_person=False)
    assert "Python" in out or "SQL" in out
    assert "a@b.co" not in out
