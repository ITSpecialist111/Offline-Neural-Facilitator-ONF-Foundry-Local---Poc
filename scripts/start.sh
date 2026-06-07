#!/usr/bin/env bash
# Cross-platform launcher for the Offline Neural Facilitator (backend + frontend).
# Works on macOS/Linux (and Windows via Git Bash / WSL).
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3}"
HOST="${ONF_HOST:-127.0.0.1}"
PORT="${ONF_PORT:-8000}"

cleanup() {
  echo "Stopping services..."
  [[ -n "${BACKEND_PID:-}" ]] && kill "${BACKEND_PID}" 2>/dev/null || true
  [[ -n "${FRONTEND_PID:-}" ]] && kill "${FRONTEND_PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starting backend (uvicorn) on ${HOST}:${PORT}..."
"${PYTHON}" -m uvicorn backend.main:app --host "${HOST}" --port "${PORT}" --reload &
BACKEND_PID=$!

echo "Starting frontend (Vite)..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

echo "Backend PID ${BACKEND_PID}, Frontend PID ${FRONTEND_PID}. Press Ctrl+C to stop."
wait
