# SkillGap — Career Intelligence Platform

## 📝 Project Overview
SkillGap is a **locally hosted, security-forward career intelligence platform** that helps users understand and close the gap between their current skills and target roles. Upload a resume, pick a role, and get skill gaps, job matches, learning resources, and a deadline-based plan — with AI running on your machine and your data staying local.

🔗 **Demo / Walkthrough Video:** https://drive.google.com/file/d/1pfgut0sNA2X1oyJbQcsR5RDQXh5jV8zU/view?usp=sharing

---

## ✨ Key Features
- **Resume upload & skill extraction** — PDF upload with PII redaction before any AI processing; skills extracted via local AI with deterministic fallbacks.
- **Role analysis** — Required / preferred / description match rates, overall match label, and identified skill gaps.
- **Job matching** — Browse synthetic job postings and see how your profile aligns.
- **Skill ontology** — Canonical and mapped skills (parent/child relationships) dynamically maintained.
- **Learning plan** — Deadline-based roadmap with approval gate and progress tracking; course completion updates your skills automatically.
- **Authentication** — Register/login/logout with JWT access/refresh tokens, HTTP-only cookies, refresh rotation, and blacklist on logout.
- **Security posture** — Resume redacted text encrypted at rest; security headers; login rate limiting; unified API error shape.
- **Quality controls** — End-to-end core flow with filtering/search, AI + fallback extraction, input validation, automated backend tests, and synthetic data only.

---

## 🏗️ Tech Stack

### Frontend
- React, TypeScript, Vite
- Tailwind CSS, React Router
- Auth via HTTP-only cookies (frontend never stores JWT)

### Backend
- FastAPI, SQLAlchemy ORM, Pydantic, Alembic
- SQLite (local)

### AI + NLP
- TinyLlama via Ollama (local HTTP)
- Timeouts + fallbacks (spaCy + dictionary/regex)

### PDF
- PyMuPDF (fitz) for text extraction

### Crypto
- AES-GCM encryption for redacted resume text at rest
- Hashed refresh tokens for blacklist storage

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js (LTS) + npm
- Ollama running locally with TinyLlama:

```bash
ollama pull tinyllama
```

Ollama’s API is expected at `http://localhost:11434` by default.

---

## 📁 Project Structure

```text
SkillGap/
├── backend/          # FastAPI app, DB, migrations, AI client, services
├── frontend/         # React + Vite + Tailwind app
├── scripts/          # Dev launcher + test runners
├── docs/             # PRD and Engineer Appendix
├── sample_jobs/      # Sample job posting PDFs (synthetic)
└── sample_courses/   # Sample course PDFs (synthetic)
```

---

## 🔧 Backend Setup

From the project root:

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` → `.env` inside `backend/` and set at least `SECRET_KEY`.

Run migrations:

```bash
alembic upgrade head
```

Start API (port 8001):

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Backend: `http://localhost:8001`

---

## 🖥️ Frontend Setup

From the project root:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

---

## ⚙️ Environment Variables

Backend reads from `backend/.env`.

| Variable | Description | Example |
|----------|-------------|---------|
| `APP_ENV` | Environment label (affects cookie behavior). | `local` |
| `SECRET_KEY` | JWT signing secret. | `long-random-string` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime. | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime. | `30` |
| `DATABASE_URL` | SQLAlchemy DB URL. | `sqlite:///./skillgap.db` |
| `OLLAMA_BASE_URL` | Ollama API base URL. | `http://localhost:11434` |
| `CORS_ORIGINS` | Allowed origins. | `http://localhost:5173` |
| `MAX_RESUME_MB` | Max resume PDF size. | `5` |
| `LOG_LEVEL` | Logging verbosity. | `info` |

---

## 🧭 App Routes

### Unauthenticated
- `/` (Landing)
- `/login`
- `/register`

### Authenticated (App Shell + Navbar)
- `/dashboard`
- `/roles`
- `/resume-skills`
- `/jobs`
- `/jobs/:jobId`
- `/skills`
- `/skills/:skillId`
- `/plan`
- `/settings`

### Dev-Only
- `/dev/jobs`
- `/dev/courses`
- `/dev/skills`

---

## 🔮 Future Development Roadmap

- **Live Job Data Integration** — Replace synthetic postings with real-time job scraping or API integrations (LinkedIn, Indeed, company career pages) while preserving PII protections.
- **Mentor Mode** — Allow mentors or career advisors to manage multiple users, review skill gaps, and co-create learning plans.
- **Single Job Deep-Dive Mode** — Upload a specific job posting and generate a hyper-targeted roadmap tailored to that exact position.
- **Adaptive Skill Recommendations** — Dynamically adjust learning paths based on user progress, performance, and time-to-deadline changes.

---

## 🧪 Testing

Backend:

```bash
pytest
pytest --cov=app
```

Frontend unit tests:

```bash
npm run test
```

E2E (Playwright):

```bash
npx playwright install
npm run e2e
```

---

## 🔒 Security Notes

- Resume text is **redacted before AI** and encrypted at rest.
- Auth uses **HTTP-only, SameSite=Strict** cookies; refresh tokens rotate and are blacklisted on logout.
- In local dev, cookies work over HTTP on localhost; for any other environment, use HTTPS and set cookie flags accordingly.

---

## 📚 Documentation

- PRD: `docs/SkillGap_PRD.md`
- Engineer Appendix: `docs/SkillGap_Engineer_Appendix.md`
