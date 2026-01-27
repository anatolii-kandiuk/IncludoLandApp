#!/usr/bin/env sh
set -eu

mkdir -p /app/media

echo "Applying database migrations..."

# Railway (and other PaaS) can start the web container before the DB is fully ready.
# Migrations are idempotent, so we can retry safely.
max_attempts="${DB_WAIT_MAX_ATTEMPTS:-30}"
attempt=1
until python manage.py migrate --noinput; do
	if [ "$attempt" -ge "$max_attempts" ]; then
		echo "Database is not ready after ${max_attempts} attempts; exiting." >&2
		exit 1
	fi
	echo "Database not ready (attempt ${attempt}/${max_attempts}); retrying in 2s..." >&2
	attempt=$((attempt + 1))
	sleep 2
done

python manage.py collectstatic --noinput || true

if [ "${1:-}" = "gunicorn" ]; then
	host="0.0.0.0"
		port="${PORT:-8080}"
	workers="${WEB_CONCURRENCY:-2}"
	shift
	exec gunicorn "$@" --bind "${host}:${port}" --workers "${workers}"
fi

exec "$@"
