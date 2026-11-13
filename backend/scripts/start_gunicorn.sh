#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ "${SKIP_ALEMBIC:-0}" != "1" ]] && [[ "${DEBUG:-false}" != "true" ]]; then
  echo "Running database migrations..."
  alembic upgrade head
fi

if [[ "${ENABLE_SEED:-false}" == "true" ]]; then
  echo "Running demo seed..."
  python -c "from app.scripts.seed import seed_demo_data; seed_demo_data()"
fi

# 在 fork worker 之前单进程初始化一次，避免多 worker 并发写库撞唯一键
echo "Bootstrapping initial data..."
python -c "from app.bootstrap import bootstrap_data; bootstrap_data()" || echo "[warn] bootstrap skipped"

exec gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  -w "${GUNICORN_WORKERS:-4}" \
  -b "0.0.0.0:${PORT:-8000}" \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
