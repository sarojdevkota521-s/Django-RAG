#!/bin/sh
set -e

echo "=========================================================="
echo " Starting Django RAG Application"
echo "=========================================================="

# Run database migrations
echo "==> Running database migrations..."
python manage.py migrate --noinput

# Collect static files for production
echo "==> Collecting static assets..."
python manage.py collectstatic --noinput --clear || true

# Start Gunicorn WSGI server
echo "==> Starting Gunicorn on port ${PORT:-8000}..."
exec gunicorn rag.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile -
