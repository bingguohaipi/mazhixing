#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

echo "Starting Judge0 sandbox..."
docker compose -f docker-compose.judge0.yml up -d

echo "Waiting for Judge0 to become healthy..."
for _ in $(seq 1 30); do
  if curl -sf http://localhost:2358/system_info >/dev/null 2>&1; then
    echo "Judge0 is ready at http://localhost:2358"
    exit 0
  fi
  sleep 2
done

echo "Judge0 did not become ready in time. Check: docker compose -f docker-compose.judge0.yml logs"
exit 1
