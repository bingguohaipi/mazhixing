#!/usr/bin/env bash
# 首次申请 Let's Encrypt 证书（需域名已解析、80 端口可访问）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

: "${DOMAIN:?Set DOMAIN, e.g. export DOMAIN=oj.example.com}"
: "${CERTBOT_EMAIL:?Set CERTBOT_EMAIL}"

CERTS_DIR="$ROOT/deploy/certs"
WWW_DIR="$ROOT/deploy/certbot-www"

mkdir -p "$CERTS_DIR" "$WWW_DIR"

echo "==> Starting temporary nginx for ACME challenge..."
docker compose -f docker-compose.prod.yml -f docker-compose.https.yml up -d frontend

echo "==> Requesting certificate for $DOMAIN ..."
docker run --rm \
  -v "$CERTS_DIR:/etc/letsencrypt" \
  -v "$WWW_DIR:/var/www/certbot" \
  certbot/certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email "$CERTBOT_EMAIL" \
  --agree-tos \
  --no-eff-email \
  -d "$DOMAIN"

echo "==> Reload nginx with TLS ..."
docker compose -f docker-compose.prod.yml -f docker-compose.https.yml up -d --force-recreate frontend

echo "Done. Certificate stored in deploy/certs/live/$DOMAIN/"
echo "Set CORS_ORIGINS=https://$DOMAIN in backend/.env"
