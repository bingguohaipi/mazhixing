#!/usr/bin/env bash
# Celery Worker 启动脚本（异步判题）
# 使用前请确保 Redis 已启动，且 .env 中 CELERY_TASK_ALWAYS_EAGER=false

set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
exec celery -A app.celery_app:celery_app worker --loglevel=info --concurrency=2
