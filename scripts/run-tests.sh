#!/usr/bin/env bash
# Run all tests (backend pytest + frontend unit). Run from repo root: ./scripts/run-tests.sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
FAILED=0

echo ""
echo "=== Backend tests (pytest) ==="
cd "$BACKEND"
if [ -d .venv ]; then . .venv/bin/activate; elif [ -d venv ]; then . venv/bin/activate; fi
python -m pytest tests -v --tb=short || FAILED=1

echo ""
echo "=== Frontend unit tests (vitest) ==="
cd "$FRONTEND"
npm run test -- --run || FAILED=1

if [ $FAILED -eq 1 ]; then
  echo ""
  echo "One or more test runs failed."
  exit 1
fi
echo ""
echo "All tests passed."
exit 0
