# Product Requirements Document (PRD) — Revised

## Product Name 
SkillGap 

---

## 1. Executive Summary
SkillGap is a locally hosted, security-forward career intelligence platform that helps users bridge the gap between their current skills and target roles. Users upload a resume PDF, select a role, and receive advisory guidance including skill gaps, recommended job matches (from synthetic postings), learning resources, and a deadline-based roadmap with persistent tracking.

The system uses **AI locally (TinyLlama via Ollama)** for structured extraction and advisory text, with deterministic fallbacks. It also maintains a growing **skill ontology** where "mapped skills" are created and maintained via AI proposals and dev overrides.

---

## 2. Goals & Non-Goals

### Goals
- Provide a serious advisory career tool with persistent tracking
- Secure authentication using JWT access/refresh with refresh rotation and blacklist
- End-to-end protection of user data, including **PII redaction before AI**
- Skill gap analysis using canonical + mapped skills
- Deadline-driven learning plan with approval gate and progress tracking
- Fully local deployment, no paid services
- CI/CD with automated API, UI, and security behavior testing

### Non-Goals
- Scalability and multi-node deployment
- Real-time scraping or third-party APIs (synthetic datasets only for v1)
- Resume version history (latest only)
- Multiple concurrent active roles
- Manual marking of a skill complete without completing at least one resource

---

## 3. Target Users
- New graduates
- Career switchers
- Mentors (future feature)

---

## 4. Core User Flow
1. User registers/logs in
2. User uploads resume (PDF)
3. System extracts text → **redacts PII** → extracts skills (AI or non-AI mode)
4. User selects target role and presses **Analyze Role**
5. System parses synthetic job posting PDFs (stored globally) and computes role aggregates
6. User views:
   - required/preferred/description match rates
   - overall match label
   - skill gaps and job matches
7. User learns via resources and builds a deadline plan
8. User tracks course completion; skills update automatically when learning branches are completed

---

## 5. Authentication & Security

### Authentication
- Register / Login / Logout
- JWT access token (short-lived) + refresh token (long-lived)
- Refresh token rotation
- HTTP-only cookies; SameSite=Strict
- Logout invalidates refresh token using blacklist (logout requires refresh cookie only)

### Password policy
- Minimum 12 chars
- Must include uppercase, lowercase, number

### Data security and protections
- Resume **redacted text encrypted at rest** (AES-GCM)
- ORM-only DB access (SQLAlchemy)
- File upload validation (PDF only)
- Rate limiting on login attempts
- Security headers enabled
- Unified API error shape:
```json
{ "error_code": "STRING_CODE", "message": "Human readable" }
```

---

## 6. Resume & Skill Extraction

### Resume upload rules
- PDF only
- Uploading a new resume:
  - **hard-deletes** prior resume
  - purges UserSkills where source = `resume`
  - keeps `manual` and `course` skills

### Extraction modes (user-controlled)
- AI mode ON: TinyLlama → spaCy → regex fallback
- AI mode OFF: spaCy → regex fallback
- Skills display **source only** (no confidence)

### Resume AI output (structured)
AI extracts:
- skills
- degree (type, graduation year)
- experience (titles, bullet points)

### PII redaction (before any AI)
Remove/redact:
- email, phone, URLs, street address (best-effort)
- personal name (first-line heuristic + spaCy PERSON NER)
- school names (partial redaction that preserves degree/year info)

---

## 7. Skill Ontology and "Mapped Skills"

### Canonical and mapped skills
- Skills exist as nodes with optional parent mapping:
  - child skill (e.g., "MySQL") → parent skill ("SQL")

### Unknown skills behavior
- If extraction returns an unknown skill:
  - it is inserted into Skills table automatically (parent null initially)

### AI parent creation / mapping proposal
- TinyLlama proposes parent mappings for new/unmapped skills:
  - "AWS RDS" → parent "SQL"
- If proposed parent doesn't exist, system may create it as a new canonical skill.
- Dev can override parent mappings via dev UI mapping editor.

No automatic adding of child skills when adding a parent to user profile.

---

## 8. Role Analysis

### Role selection
- Standard search (no regex mode)
- One active role at a time
- Default active role = most recently selected role

### Analyze Role
- Only runs when user presses **Analyze Role**
- Parses synthetic job PDFs and stores results globally for reuse across users

---

## 9. Dashboard

### Displayed metrics
- Required match %
- Preferred match %
- Description match %
- Overall match label derived from internal weighted score (Developing/Competitive/Ready)
- Missing skills count
- Recommended job matches count
- Deadline status
- Global popular skills and role-needed skills
- Short advisory text (AI, constrained length)

Navbar:
- Dashboard, Roles, Skills, Jobs, Plan, Settings

---

## 10. Job Matches

- Ranked jobs by internal weighted match score
- Filters: degree, experience, "what you will be doing" match
- Job card has dropdown showing all missing skills
- "I have this skill" action adds missing skill as manual from jobs page
- Job details show trimmed "what you will be doing" excerpt

---

## 11. Skill Gap

- Shows missing canonical skills and mapped skills
- Filters/sorts include frequency and type
- "Not Interested" toggle is **global across roles**
- "I have this skill" adds manual skill immediately
- Links to Learning Resources

---

## 12. Learning Resources / Skill Detail

- Course cards show:
  - difficulty, format, popularity, duration
  - per-user adjusted difficulty stored (UserCourseMeta)
- Branch completion rule:
  - skill is auto-added when unfinished resources for that skill reaches **0**
- Skill completion requires at least one resource completion

---

## 13. Learning Plan Builder

- Deadline-driven plan creation
- Default 5 hrs/week
- Proposal gate: user approves/denies skills before plan is built
- Greedy fit algorithm for v1
- Linear plan with:
  - reorder skills
  - swap interchangeable resources
- One active plan per role; switching roles auto-switches plan

---

## 14. Synthetic Data Ingestion (Dev Tools)

### Dev-only access
- Use role `dev` (not admin)

### Dev ingestion UI
- Bulk upload synthetic job posting PDFs
- Upload courses.json
- AI derives canonical role from posting; fallback exists
- Dev can manually override role assignment
- Dev can delete job postings (hard delete)

### Plug-in readiness (future)
- Web scraper / job APIs
- Enterprise AI models

---

## 15. Technology Choices (Locked)
- Frontend: React + TypeScript + Tailwind
- Backend: FastAPI + SQLAlchemy + Alembic
- DB: SQLite
- PDF extraction: PyMuPDF (fitz)
- AI runtime: TinyLlama via Ollama + spaCy fallback + regex
- Testing: pytest/httpx + Playwright
- CI/CD: GitHub Actions, separate workflows

---

## 16. CI/CD & Testing

Included:
- Unit tests
- API integration tests
- UI E2E tests (Playwright)
- Security behavior tests
- Coverage report (informational)
- Build artifacts
- E2E runs on every push to main
- Separate workflow files (backend/frontend/e2e/security)

Excluded:
- Lint/format gating
- mypy gating
- coverage threshold enforcement

---

## 17. Tradeoffs
- PII redaction reduces edge-case extraction nuance but strengthens privacy posture
- Synthetic datasets limit realism; architecture supports future plug-ins
- Global aggregates shared across users, computed only when Analyze Role is pressed
- One active role at a time for user simplicity

---

## 18. Future Roadmap
- Job favoriting/prioritization (human + AI-assisted)
- Single job posting upload and roadmap around that posting
- Mentor role (manage multiple users)
- Plug-ins: web scraper/job APIs + enterprise AI
