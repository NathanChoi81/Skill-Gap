# Engineer Appendix — SkillGap

## A0) Locked Tech Stack & Runtime

### Frontend
- React + TypeScript (Vite)
- Tailwind CSS
- React Router
- Auth via HTTP-only cookies (frontend never stores JWT)
- **Landing page**: no navbar; login/register only. **App shell with navbar** (Dashboard, Roles, Jobs, Skills, Plan, Settings; Dev when role=dev) shown only after login. Logout redirects to landing.

### Backend
- FastAPI (Python)
- SQLAlchemy ORM
- Pydantic models
- Alembic migrations

### Database
- SQLite (local file)

### AI + NLP
- TinyLlama via **Ollama** (HTTP calls from backend)
- spaCy fallback
- Regex dictionary fallback (lowest tier)
- Timeouts for AI calls (hard cutoff)

### PDF Text Extraction
- PyMuPDF (fitz)

### Crypto
- AES-GCM encryption for **redacted** resume text at rest
- Refresh tokens stored as hashes in blacklist (never store raw refresh token)

### Testing / CI
- pytest + httpx (unit + integration)
- Playwright (E2E UI tests)
- Security behavior tests (pytest marker)
- Coverage report generated (no threshold gate)
- GitHub Actions, **separate** workflow files
- E2E runs on every push to main

### Deployment & TLS
- **Local dev** (`APP_ENV=local` or equivalent): HTTP allowed for `localhost` / `127.0.0.1` only. Cookie `Secure` flag off when origin is localhost so auth works over HTTP.
- **All other environments** (staging, production, or any non-localhost host): **HTTPS only**. Backend and frontend served over HTTPS (direct or reverse proxy). `CORS_ORIGINS` and redirects use `https://`. Cookies always `Secure` and `SameSite=Strict`. Reject or redirect HTTP requests.

---

## A1) Auth Model & Cookie Strategy

### Tokens
- Access token (short-lived)
- Refresh token (longer-lived, rotates on refresh)
- HTTP-only Secure cookies, SameSite=Strict

### Logout rule
- `POST /auth/logout` succeeds with refresh cookie only (no access token required)
- Logout blacklists refresh token and clears cookies

### Password policy
- min 12 chars
- at least 1 uppercase, 1 lowercase, 1 number

---

## A2) API Contract

### Standard error shape
```json
{ "error_code": "STRING_CODE", "message": "Human readable" }
```

### Auth (no access token required)
**POST `/auth/register`**
```json
{ "email": "string", "password": "string" }
```
200: sets auth cookies (session established); returns user. Frontend redirects to Dashboard.
```json
{ "user": { "id": 1, "email": "string" } }
```
409: email exists

**POST `/auth/login`**
```json
{ "email": "string", "password": "string" }
```
200: sets cookies  
401: invalid credentials  
429: rate limited

**POST `/auth/refresh`**
- uses refresh cookie
- returns new access cookie
401: invalid/blacklisted refresh

**POST `/auth/logout`**
- uses refresh cookie only
- blacklists refresh token hash
- clears cookies

---

### User (access token required)
**GET `/me`**
```json
{ "id": 1, "email": "string", "active_role_id": 5 }
```

---

### Resumes (access token required)
**POST `/resumes/upload`** (multipart)
- `file` (PDF)
- `use_ai` (bool)

200:
```json
{
  "resume_id": 3,
  "extracted_skills": [{ "name": "MySQL", "source": "ai" }],
  "mapped_skills": [{ "canonical": "SQL", "children": ["MySQL"] }]
}
```

Behavior:
- hard delete previous resume
- purge `user_skills` where source=`resume`
- keep manual/course skills

**DELETE `/resumes/current`**
- deletes current resume
- purges resume-sourced skills

---

### Skills (access token required)
**GET `/skills/my`**
Returns canonical skills user has, plus `source`.

**GET `/skills/search?q=&limit=30`**
Returns skills (canonical) matching name, for manual-add typeahead.

**GET `/skills/{skill_id}`**
Returns `{ "id", "name" }` for display (e.g. Skill Detail page).

**POST `/skills/add`**
```json
{ "skill_id": 12, "source": "manual" }
```

**POST `/skills/remove`**
```json
{ "skill_id": 12 }
```

**POST `/skills/not-interested`** (global)
```json
{ "skill_id": 12, "value": true }
```

---

### Roles (access token required)
**GET `/roles/search?q=backend`**
```json
[{ "id": 1, "name": "Backend Engineer" }]
```

**GET `/roles/my`**
User's role history (roles they have selected), most recent first.
```json
[{ "id": 1, "name": "Backend Engineer", "last_selected_at": "2025-03-01T12:00:00" }]
```

**POST `/roles/select`**
```json
{ "role_id": 1 }
```
Sets active role. One active role at a time.

**POST `/roles/{role_id}/analyze`**
- parses synthetic job PDFs for that role if not already parsed
- computes/stores global role aggregates
- does NOT run automatically; only when user presses Analyze Role

**GET `/roles/{role_id}/summary`**
```json
{
  "required_match": 70,
  "preferred_match": 40,
  "description_match": 55,
  "internal_score": 62,
  "label": "Competitive",
  "missing_count": 4,
  "recommended_jobs": 7
}
```

---

### Jobs (access token required)
**GET `/roles/{role_id}/jobs`**
Query params: `sort`, `degree`, `experience`, `desc_match`
Returns job cards with match label, missing preview, and full missing list for dropdown.

**GET `/jobs/{job_id}`**
Returns job detail (trimmed excerpt + skills buckets).

---

### Gaps (access token required)
**GET `/roles/{role_id}/gaps`**
Query: `sort`, `type_filter`, `search`
Returns missing canonical + mapped skills excluding global not-interested.

---

### Courses (access token required)
**GET `/skills/{skill_id}/courses`**
Returns course list with adjusted difficulty (from user_course_meta if present).

**POST `/courses/{course_id}/status`**
```json
{ "status": "in_progress" | "complete" }
```

Branch rule:
- Skill auto-added when unfinished resources for that skill reaches **0**
- Skill completion requires at least one resource completion

---

### Plan (access token required)
**POST `/plan/propose`**
```json
{ "deadline": "YYYY-MM-DD", "hours_per_week": 5 }
```
- API always receives a single **deadline** as `YYYY-MM-DD`. Frontend may collect it in three ways: **weeks from today**, **months from today**, or **explicit date picker**; frontend converts to date before sending.
- Validation: `deadline >= today + 7 days` (and optionally cap at e.g. 2 years).
Returns proposed skills list, with estimated hours.

**POST `/plan/confirm`**
```json
{ "skills": [12, 15, 18], "ordering": [12, 18, 15] }
```

**GET `/plan/current`**
Returns active plan for active role.

**PATCH `/plan/current`**
```json
{ "status": "active" | "paused" }
```
Pause or resume the current plan.

---

### Dev (role=dev required)
All endpoints under `/dev/*`.

**GET `/dev/jobs`**
List job postings with parsed data summary (id, title_original, role_id, role_name, degree_required, experience_required).

**PATCH `/dev/jobs/{job_id}`**
```json
{ "role_id": 1 }
```
Override job's role.

**POST `/dev/jobs/upload`** (multipart, multi-PDF)
- AI extracts title_original + role_canonical + skills buckets + excerpt
- fallback exists
- role can be overridden in UI

**DELETE `/dev/jobs/{job_id}`**
Hard delete job posting.

**POST `/dev/courses/upload`**
Upload `courses.json` to populate courses table.

**GET `/dev/skills/unmapped`**
List skills with `parent_skill_id IS NULL` (excluding obvious canonical nodes if desired)

**POST `/dev/skills/map`**
```json
{ "child_skill_id": 22, "parent_skill_id": 5 }
```

**POST `/dev/skills/propose-mappings`**
Runs TinyLlama mappings schema and applies suggestions (with safe rules; can require dev review).

---

## A3) Database Schema (DDL-level)

### users
- id PK
- email UNIQUE NOT NULL
- password_hash NOT NULL
- role NOT NULL DEFAULT "user"  (dev role allowed)
- created_at NOT NULL

### token_blacklist
- id PK
- refresh_token_hash UNIQUE NOT NULL
- expires_at NOT NULL
- created_at NOT NULL

### resumes
- id PK
- user_id FK UNIQUE NOT NULL (one resume per user)
- encrypted_redacted_text NOT NULL
- uploaded_at NOT NULL

### skills
- id PK
- name UNIQUE NOT NULL
- parent_skill_id FK NULL (mapped skill parent)
- category NOT NULL DEFAULT "hard"

### user_skills
- user_id FK
- skill_id FK
- source NOT NULL (resume/manual/course)
- created_at
PK (user_id, skill_id)

### user_not_interested_skills
- user_id FK
- skill_id FK
- created_at
PK (user_id, skill_id)

### roles
- id PK
- name UNIQUE NOT NULL
- created_at

### user_roles
- user_id FK
- role_id FK
- last_selected_at
PK (user_id, role_id)

### user_active_role
- user_id PK FK
- role_id FK
- set_at

### job_postings
- id PK
- role_id FK
- title_original NOT NULL
- pdf_text NOT NULL
- degree_required NULL
- experience_required NULL
- what_you_will_do_excerpt NULL
- derived_by NOT NULL (ai/fallback/manual_override)
- created_at

### job_skills
- job_id FK
- skill_id FK
- skill_type NOT NULL (required/preferred/description)
PK (job_id, skill_id, skill_type)

### role_aggregates
- role_id PK FK
- aggregated_skill_frequency_json NOT NULL
- computed_at NOT NULL

### courses
- id PK
- title NOT NULL
- skill_id FK
- difficulty INT NOT NULL (1–5)
- duration_hours REAL NOT NULL
- format NOT NULL
- popularity_score INT NOT NULL
- url NULL

### user_course_progress
- user_id FK
- course_id FK
- status NOT NULL (in_progress/complete)
- updated_at
PK (user_id, course_id)

### user_course_meta
- user_id FK
- course_id FK
- adjusted_difficulty INT NOT NULL (1–5)
- updated_at
PK (user_id, course_id)

### plans
- id PK
- user_id FK
- role_id FK
- deadline_date NOT NULL
- hours_per_week INT NOT NULL DEFAULT 5
- status NOT NULL (active/paused)
UNIQUE (user_id, role_id)
- created_at

### plan_skills
- plan_id FK
- skill_id FK
- position INT NOT NULL
PK (plan_id, skill_id)

### plan_skill_courses
- plan_id FK
- skill_id FK
- course_id FK
- selected BOOL NOT NULL
PK (plan_id, skill_id, course_id)

---

## A4) AI JSON Schemas

### Resume extraction (TinyLlama)
```json
{
  "skills": ["string"],
  "degree": { "type": "string|null", "graduation_year": "string|null" },
  "experience": [{ "title": "string|null", "bullets": ["string"] }]
}
```

### Job extraction (TinyLlama)
```json
{
  "title_original": "string",
  "role_canonical": "string",
  "degree_required": "string|null",
  "experience_required": "string|null",
  "what_you_will_do_excerpt": "string|null",
  "skills": {
    "required": ["string"],
    "preferred": ["string"],
    "description": ["string"]
  }
}
```

### Parent mapping proposal (TinyLlama)
```json
{
  "mappings": [
    { "child": "string", "parent": "string|null", "category": "hard|soft|null" }
  ]
}
```

Failure → fallback if:
- invalid JSON
- missing required keys/arrays
- timeout exceeded

---

## A5) PII Redaction Spec (Pre-AI)

Redact:
- emails, phones, URLs
- addresses (best-effort)
- school names (partial replace with `[REDACTED_SCHOOL]`)
- person names:
  - first-line heuristic + spaCy PERSON NER spans

Preserve:
- degree type/year
- courses
- skills
- experience bullets (minus identifiers)

Logging:
- counts only, never content

---

## A6) Match Scoring & Display

### Displayed on dashboard/job
- required_match%
- preferred_match%
- description_match%

### Internal weighted score (used for label + ranking)
`score = 100 * (0.60*req_cov + 0.25*pref_cov + 0.15*desc_cov)`

Label thresholds:
- 0–49 Developing
- 50–79 Competitive
- 80–100 Ready

---

## A7) Plan Generation Algorithm

### Deadline input (UI)
- User may specify the deadline in one of three ways; frontend sends a single date to the API:
  - **Weeks**: "Finish in N weeks" (e.g. 1–104). Compute `deadline = today + N weeks`.
  - **Months**: "Finish in N months" (e.g. 1–24). Compute `deadline = today + N calendar months`.
  - **By date**: Date picker "Finish by [date]" with min = today + 7 days.
- Show the resulting target date in plain text (e.g. "Target date: 2026-03-15") so the user sees the resolved date.

Inputs (backend):
- deadline D (YYYY-MM-DD)
- hours/week H (default 5)
- gaps excluding not-interested
- hours(skill) = sum(selected course durations)

Priority:
`priority(s) = freq(s) * type_weight(s)`  
type weights: required 1.0, preferred 0.6, description 0.3

Greedy fit into `budget_hours = weeks_until_deadline * H`.

Approval gate:
- user can deselect + reorder
- then plan persisted

Edge cases:
- if budget too small for even top skill: propose top skill anyway + warning
- if role not analyzed: block and prompt analyze
- if no resume: allow but warn

---

## A8) Dev Ingestion UI

Routes:
- `/dev/jobs` bulk upload PDFs
- `/dev/courses` upload courses.json
- `/dev/skills` mapping editor + AI propose mappings
- Dev can override role_canonical per job
- Dev can hard delete job postings
- Role aggregates recompute only on Analyze Role click

---

## A9) CI/CD Workflow Spec

### Separate workflow files
- `backend.yml`: pytest + coverage report
- `frontend.yml`: build frontend
- `e2e.yml`: start backend+frontend, run Playwright (every push to main)
- `security.yml`: pytest markers for security behavior checks

### Fixtures
- skills seed
- courses.json
- synthetic job PDFs for ingestion tests

### E2E critical path tests
1) Register → Login
2) Upload resume (AI off) → skills appear
3) Select role → Analyze → summary updates
4) Jobs → add skill manually
5) Gap → not interested global toggle
6) Skill detail → complete branch → skill auto-added
7) Plan propose → approve skills → plan created

---

## A10) Page Specifications

### 1. Landing Page (Public)
- **Purpose:** Introduce the product and drive registration/login.
- **Components:** Centered logo; headline: “You’re one skill away from your dream job, what’s stopping you?”; feature tiles (Resume Upload, Skill Gap Analysis, Job Matches, Learning Resources, Career Tracking); CTA buttons: Register, Login.
- **No API calls.**

### 2. Register Page
- **Purpose:** Create account and establish session.
- **Fields:** Email, Password, Confirm Password.
- **Validation:** 12+ chars; uppercase, lowercase, number; email format; password match.
- **Action:** POST /auth/register; redirect → Dashboard.

### 3. Login Page
- **Purpose:** Authenticate user.
- **Fields:** Email, Password.
- **Action:** POST /auth/login; on success → Dashboard. Rate limiting applied (backend).

### 4. Dashboard
- **Purpose:** Central advisory hub for active role.
- **Displays:** Required match %, Preferred match %, Description match %, Overall match label, Missing skills count, Recommended jobs count, Deadline status, Most-needed skills (role), Global popular skills, AI advisory summary.
- **Navigation:** Dashboard, Roles, Skills, Jobs, Plan, Settings.

### 5. Roles Page
- **Purpose:** Search and manage target roles.
- **Components:** Role search bar; role list results; “Analyze Role” button; user role history list; set active role.
- **Action:** POST /roles/{role_id}/analyze.

### 6. Resume & Skills Page
- **Purpose:** Manage resume and skill profile.
- **Components:** Resume PDF upload; AI mode toggle; extracted skills list (with source); mapped skills grouping; manual skill add; remove skill; source filter.
- **Behavior:** Hard delete previous resume; purge resume-sourced skills only.

### 7. Job Matches Page
- **Purpose:** Show ranked job postings for active role.
- **Components:** Sort dropdown; filters (degree, experience, description match); job cards (match label, missing skills preview, inline dropdown for full missing list, “I have this skill” button, view details).

### 8. Skill Gap Page
- **Purpose:** Explore and manage missing skills.
- **Components:** Missing skills table; sort by frequency/alphabetical/impact; filters by type (required/preferred/description); search; “Not Interested” toggle (global); “I have this skill” action.

### 9. Skill Detail / Learning Resources Page
- **Purpose:** Learn a specific skill.
- **Displays:** Skill name; importance (frequency); required/preferred context; resource list (difficulty, duration, popularity); adjusted difficulty; mark in progress; mark complete.
- **Rule:** Skill auto-added when unfinished resources = 0.

### 10. Learning Plan Page
- **Purpose:** Deadline-driven roadmap builder.
- **Flow:** Set deadline + hours/week; proposed skills list; approval gate (remove/reorder); final roadmap display.
- **Displays:** Ordered skill sequence; resource selection per skill; progress tracking; pause/resume plan.

### 11. Dev Ingestion Pages (Dev Role Only)
- **/dev/jobs:** Upload synthetic job PDFs; view parsed data; override role; delete job.
- **/dev/courses:** Upload courses.json.
- **/dev/skills:** View unmapped skills; set parent mappings; trigger AI mapping proposals.
