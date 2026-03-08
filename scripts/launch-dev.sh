#!/usr/bin/env bash
# Launch backend and frontend in background. Run from repo root: ./scripts/launch-dev.sh. Ctrl+C kills both.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

# Free port 8001 so the new backend can bind
if command -v lsof >/dev/null 2>&1; then
  PIDS=$(lsof -ti :8001 2>/dev/null || true)
  if [ -n "$PIDS" ]; then
    echo "Stopping existing process on port 8001..."
    echo "$PIDS" | xargs kill -9 2>/dev/null || true
    sleep 1
  fi
fi

cleanup() {
  echo "Stopping backend and frontend..."
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM

cd "$BACKEND"
if [ -d .venv ]; then . .venv/bin/activate; elif [ -d venv ]; then . venv/bin/activate; fi
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001 &
BACKEND_PID=$!

sleep 2
cd "$FRONTEND"
npm run dev &
FRONTEND_PID=$!

echo "Backend: http://localhost:8001"
echo "Frontend: http://localhost:5173"
echo "Press Ctrl+C to stop both."
wait
