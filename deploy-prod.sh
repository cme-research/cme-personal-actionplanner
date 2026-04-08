#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ENV_FILE=".env.prod"

# --- Preflight checks ---

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: $ENV_FILE not found."
    echo "Copy .env.prod.example to .env.prod and fill in your values:"
    echo "  cp .env.prod.example .env.prod"
    exit 1
fi

# shellcheck source=/dev/null
source "$ENV_FILE"

if [ "${DJANGO_SECRET_KEY:-}" = "change-me-run-python3-c-import-secrets-print-secrets-token-urlsafe-64" ]; then
    echo "ERROR: DJANGO_SECRET_KEY is still the placeholder value."
    echo "Generate one with: python3 -c \"import secrets; print(secrets.token_urlsafe(64))\""
    exit 1
fi

if [ "${DJANGO_SUPERUSER_PASSWORD:-}" = "change-me-to-a-strong-password" ]; then
    echo "ERROR: DJANGO_SUPERUSER_PASSWORD is still the placeholder value."
    exit 1
fi

echo "==> Building and starting containers..."
docker compose --env-file "$ENV_FILE" up --build -d

echo "==> Running database migrations..."
docker compose exec web python manage.py migrate --noinput

echo "==> Seeding default topics..."
docker compose exec web python manage.py seed_topics

echo "==> Creating superuser (skipped if already exists)..."
docker compose exec \
    -e DJANGO_SUPERUSER_USERNAME="${DJANGO_SUPERUSER_USERNAME}" \
    -e DJANGO_SUPERUSER_EMAIL="${DJANGO_SUPERUSER_EMAIL}" \
    -e DJANGO_SUPERUSER_PASSWORD="${DJANGO_SUPERUSER_PASSWORD}" \
    web python manage.py createsuperuser --noinput 2>/dev/null \
    && echo "    Superuser created." \
    || echo "    Superuser already exists, skipping."

echo "==> Collecting static files..."
docker compose exec web python manage.py collectstatic --noinput

echo ""
echo "Deployment complete. The app is running at http://localhost:8000"
echo "Make sure your reverse proxy (nginx/caddy) is configured to forward traffic."
