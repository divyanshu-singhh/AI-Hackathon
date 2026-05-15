#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Starting backend at http://localhost:8000"
bash "$ROOT_DIR/scripts/run_backend.sh" &
BACKEND_PID=$!

echo "Starting frontend at http://localhost:5173"
bash "$ROOT_DIR/scripts/run_frontend.sh" &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "Press Ctrl+C to stop both."

trap 'kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true' INT TERM EXIT
wait
