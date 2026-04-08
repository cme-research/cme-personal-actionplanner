#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ENV_FILE=".env.prod"

# --- Preflight checks ---

if [ ! -f "$ENV_FILE" ]; then
    echo "$ENV_FILE not found. Generating from template..."
    if [ ! -f .env.prod.example ]; then
        echo "ERROR: .env.prod.example not found either."
        exit 1
    fi

    GENERATED_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
    GENERATED_SUPERUSER_PW=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")

    sed \
        -e "s|change-me-run-python3-c-import-secrets-print-secrets-token-urlsafe-64|${GENERATED_SECRET_KEY}|" \
        -e "s|change-me-to-a-strong-password|${GENERATED_SUPERUSER_PW}|" \
        .env.prod.example > "$ENV_FILE"

    echo "    Generated $ENV_FILE with random secrets."
    echo "    IMPORTANT: Edit $ENV_FILE to set DJANGO_ALLOWED_HOSTS and DJANGO_SUPERUSER_EMAIL."
    echo "    Superuser password: ${GENERATED_SUPERUSER_PW}"
    echo "    (save this somewhere safe — it won't be shown again)"
    echo ""
    echo "    Re-run this script when ready."
    exit 0
fi

# shellcheck source=/dev/null
source "$ENV_FILE"

if [ "${DJANGO_SECRET_KEY:-}" = "change-me-run-python3-c-import-secrets-print-secrets-token-urlsafe-64" ]; then
    echo "ERROR: DJANGO_SECRET_KEY is still the placeholder value."
    echo "Delete .env.prod and re-run this script to auto-generate, or set it manually."
    exit 1
fi

if [ "${DJANGO_SUPERUSER_PASSWORD:-}" = "change-me-to-a-strong-password" ]; then
    echo "ERROR: DJANGO_SUPERUSER_PASSWORD is still the placeholder value."
    echo "Delete .env.prod and re-run this script to auto-generate, or set it manually."
    exit 1
fi

if [ "${DJANGO_ALLOWED_HOSTS:-}" = "yourdomain.com,www.yourdomain.com" ]; then
    echo "WARNING: DJANGO_ALLOWED_HOSTS is still the example value."
    echo "         Edit .env.prod to set your actual domain before going live."
    echo ""
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
