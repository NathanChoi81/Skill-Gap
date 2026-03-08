# SkillGap

SkillGap is a locally hosted, security-forward career intelligence platform that helps users understand and close the gap between their current skills and target roles.

- **backend/**: FastAPI + SQLAlchemy + SQLite, auth (JWT + HTTP-only cookies), resume upload with PII redaction and AI/fallback extraction, roles, jobs, gaps, courses, plan, and dev job/course upload. AI via TinyLlama (Ollama).
- **frontend/**: React + TypeScript + Vite + Tailwind. Landing (login/register, no navbar); app shell with navbar after login; Dashboard, Roles, Jobs, Skills, Plan, Settings, and Dev pages.

## Prerequisites

- Python 3.11+
- Node.js (LTS) and npm
- Ollama running locally with TinyLlama model (`ollama pull tinyllama`). API at `http://localhost:11434`.

## Backend setup

1. From the project root:
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # or: source .venv/bin/activate   # macOS/Linux
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and set at least `SECRET_KEY` (and optionally `OLLAMA_BASE_URL`, `CORS_ORIGINS`, `MAX_RESUME_MB`).
3. Run migrations (from `backend/`):
   ```bash
   alembic upgrade head
   ```
4. Start the API:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

Backend runs at `http://localhost:8000`.

## Frontend setup

1. From the project root:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
2. Open `http://localhost:5173`. The dev server proxies API requests to the backend.

## Scripts (`scripts/`)

Run from the **project root** (same directory as this README).

- **Launch backend + frontend together**
  - Windows: `.\scripts\launch-dev.ps1` — opens two PowerShell windows (backend and frontend).
  - macOS/Linux: `./scripts/launch-dev.sh` — runs both in one terminal; press Ctrl+C to stop both.
- **Run all tests** (backend pytest + frontend unit tests)
  - Windows: `.\scripts\run-tests.ps1`
  - macOS/Linux: `./scripts/run-tests.sh`

## Documentation (`docs/`)

- **Product Requirements Document (PRD):** `docs/SkillGap_PRD.md`
- **Engineer Appendix:** `docs/SkillGap_Engineer_Appendix.md`

## Running tests manually

- **Backend** (from `backend/`):
  ```bash
  pytest
  pytest --cov=app  # coverage report
  ```
- **Frontend E2E** (from `frontend/`): Start backend and frontend first (e.g. run `.\scripts\launch-dev.ps1` or `./scripts/launch-dev.sh`), then:
  ```bash
  npx playwright install
  npm run e2e
  ```
