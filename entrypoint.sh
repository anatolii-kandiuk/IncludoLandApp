#!/usr/bin/env sh
set -eu

if [ -z "${DATABASE_URL:-}" ] && [ -z "${DATABASE_PUBLIC_URL:-}" ] && [ -z "${PGHOST:-}" ] && [ -z "${DB_HOST:-}" ]; then
	echo "WARNING: No database environment variables found (DATABASE_URL/DATABASE_PUBLIC_URL/PGHOST/DB_HOST). The app may fail to start." >&2
fi

echo "Applying database migrations..."

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

if [ "${CREATE_DEFAULT_SUPERUSER:-1}" = "1" ]; then
	echo "Ensuring default superuser exists..."
	python manage.py create_default_superuser
fi

if [ "${1:-}" = "gunicorn" ]; then
	host="0.0.0.0"
		port="${PORT:-8080}"
	workers="${WEB_CONCURRENCY:-2}"
	shift
	exec gunicorn "$@" --bind "${host}:${port}" --workers "${workers}"
fi

exec "$@"
