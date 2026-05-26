#!/usr/bin/env zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

pm2 delete missing-pet-image-server missing-pet-server missing-pet-ai-server missing-pet-ai-worker || true
pm2 save
pm2 status
