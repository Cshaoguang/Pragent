#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ -f "$ROOT_DIR/.frontend.pid" ]]; then
  FRONTEND_PID="$(cat "$ROOT_DIR/.frontend.pid")"
  if kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" || true
    sleep 1
    kill -9 "$FRONTEND_PID" 2>/dev/null || true
  fi
  rm -f "$ROOT_DIR/.frontend.pid"
fi

pkill -f "vite.*5173" 2>/dev/null || true

echo "[stop] stopping docker services..."
docker compose down

echo "[done] all services stopped"
