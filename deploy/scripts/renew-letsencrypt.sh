#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CERTS_DIR="$ROOT/deploy/certs"
WWW_DIR="$ROOT/deploy/certbot-www"

docker run --rm \
  -v "$CERTS_DIR:/etc/letsencrypt" \
  -v "$WWW_DIR:/var/www/certbot" \
  certbot/certbot renew

docker compose -f "$ROOT/docker-compose.prod.yml" -f "$ROOT/docker-compose.https.yml" exec frontend nginx -s reload

echo "Certificate renewed."
