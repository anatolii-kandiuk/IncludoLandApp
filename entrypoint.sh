#!/usr/bin/env sh
set -eu

mkdir -p /app/media

python manage.py migrate --noinput
python manage.py collectstatic --noinput || true

if [ "${1:-}" = "gunicorn" ]; then
	host="0.0.0.0"
		port="${PORT:-8080}"
	workers="${WEB_CONCURRENCY:-2}"
	shift
	exec gunicorn "$@" --bind "${host}:${port}" --workers "${workers}"
fi

exec "$@"
