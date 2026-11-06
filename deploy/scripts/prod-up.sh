#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="$ROOT_DIR/backend/.env"
EXAMPLE="$ROOT_DIR/backend/.env.production.example"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "backend/.env not found — copying from .env.production.example"
  cp "$EXAMPLE" "$ENV_FILE"
  echo ""
  echo "Please edit backend/.env (SECRET_KEY, CORS_ORIGINS, OPENAI_API_KEY, SMS, etc.)"
  echo "Then run: python backend/scripts/check_production_env.py"
  exit 1
fi

echo "Running production env check..."
python3 "$ROOT_DIR/backend/scripts/check_production_env.py" || {
  echo "Fix backend/.env before deploying."
  exit 1
}

echo "Starting production stack (MySQL, Redis, Judge0, Backend, Celery, Frontend)..."
docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo "Optional monitoring (Prometheus + Grafana):"
echo "  docker compose -f docker-compose.prod.yml -f docker-compose.monitoring.yml up -d"

echo ""
echo "Waiting for app health (via Nginx)..."
for _ in $(seq 1 40); do
  if curl -sf http://127.0.0.1:8080/health >/dev/null 2>&1; then
    echo "App is ready: http://127.0.0.1:8080"
    echo "Public (after firewall): http://<your-public-ip>:8080"
    exit 0
  fi
  sleep 3
done

echo "Stack started but health check timed out. Run: docker compose -f docker-compose.prod.yml logs backend frontend"
exit 1
