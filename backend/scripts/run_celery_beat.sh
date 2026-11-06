#!/usr/bin/env bash
# Celery Beat — 每日凌晨刷新排行榜快照
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
exec celery -A app.celery_app:celery_app beat --loglevel=info
