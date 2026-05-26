#!/usr/bin/env zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f ".env" ]]; then
  echo "[ERROR] .env not found at project root"
  exit 1
fi

if [[ ! -x "ai_server/.venv/bin/uvicorn" ]]; then
  echo "[ERROR] ai_server/.venv/bin/uvicorn not found or not executable"
  exit 1
fi

if [[ ! -x "ai_server/.venv/bin/python" ]]; then
  echo "[ERROR] ai_server/.venv/bin/python not found or not executable"
  exit 1
fi

pm2 start ecosystem.config.cjs

echo "[INFO] waiting for services to boot..."
sleep 4

echo "[INFO] health check: ai_server"
curl -sf http://127.0.0.1:8000/health > /dev/null

echo "[INFO] health check: image_server"
curl -sf http://127.0.0.1:18080/ > /dev/null

pm2 status
echo "[OK] PM2 one-click test stack is up"
