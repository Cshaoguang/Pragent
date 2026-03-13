#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

mkdir -p data/storage

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

echo "[start] launching docker services..."
docker compose up -d mysql redis qdrant backend

echo "[start] launching frontend..."
cd "$ROOT_DIR/frontend"
if [[ ! -d node_modules ]]; then
  npm install
fi

if [[ -f "$ROOT_DIR/.frontend.pid" ]] && kill -0 "$(cat "$ROOT_DIR/.frontend.pid")" 2>/dev/null; then
  echo "[start] frontend already running (pid $(cat "$ROOT_DIR/.frontend.pid"))"
else
  nohup npm run dev -- --host 0.0.0.0 --port 5173 > "$ROOT_DIR/.frontend.log" 2>&1 &
  echo $! > "$ROOT_DIR/.frontend.pid"
  echo "[start] frontend started (pid $(cat "$ROOT_DIR/.frontend.pid"))"
fi

echo "[ready] backend: http://localhost:9090"
echo "[ready] frontend: http://localhost:5173"
