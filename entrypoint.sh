#!/usr/bin/env sh
set -e

# Railway sets PORT; default to 8000 for local runs.
: "${PORT:=8000}"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn includoland.wsgi:application \
  --bind "0.0.0.0:${PORT}" \
  --workers "${GUNICORN_WORKERS:-2}" \
  --threads "${GUNICORN_THREADS:-4}" \
  --timeout "${GUNICORN_TIMEOUT:-120}"
