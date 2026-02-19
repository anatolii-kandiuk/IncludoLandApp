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

# Check and train ML models if enabled
if [ "${TRAIN_ML_MODELS:-0}" = "1" ]; then
	echo "Checking ML model availability..."
	if [ -d "ml_models" ] && [ "$(ls -A ml_models/*.joblib 2>/dev/null | wc -l)" -gt 0 ]; then
		echo "ML models found, skipping training."
	else
		echo "Training ML models for all game types..."
		python manage.py train_ml_model --all-game-types --min-entries=3 || {
			echo "WARNING: ML model training failed. Models will be trained on first prediction request." >&2
		}
	fi
fi

if [ "${1:-}" = "gunicorn" ]; then
	host="0.0.0.0"
		port="${PORT:-8080}"
	workers="${WEB_CONCURRENCY:-2}"
	shift
	exec gunicorn "$@" --bind "${host}:${port}" --workers "${workers}"
fi

exec "$@"
