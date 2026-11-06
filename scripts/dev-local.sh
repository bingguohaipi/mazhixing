#!/usr/bin/env bash
# 本机开发：SQLite + 同步判题，不依赖 Docker 内 Judge0/Redis
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_LOCAL="$ROOT/backend/.env.local"
EXAMPLE="$ROOT/backend/.env.local.example"

if [[ ! -f "$ENV_LOCAL" ]]; then
  echo "Creating backend/.env.local from example..."
  cp "$EXAMPLE" "$ENV_LOCAL"
fi

echo "Backend:  http://127.0.0.1:8001  (loads .env + .env.local)"
echo "Frontend: http://127.0.0.1:3000"
echo "Stop with Ctrl+C in each terminal."
echo ""
echo "Terminal 1: npm run dev:backend"
echo "Terminal 2: npm run dev"
