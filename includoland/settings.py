import os
from pathlib import Path

import dj_database_url


BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env for local/dev runs
try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / '.env')
except Exception:
    pass

SECRET_KEY = os.getenv('SECRET_KEY')

DEBUG = os.getenv('DEBUG', '1').lower() not in {'0', 'false', 'no'}

if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-local-dev'
    else:
        raise RuntimeError('SECRET_KEY must be set in production.')

# Railway + local defaults (can be overridden via ALLOWED_HOSTS env var)
DEFAULT_ALLOWED_HOSTS = [
    'includolandapp-production.up.railway.app',
    '.railway.app',
    'localhost',
    '127.0.0.1',
]

raw_allowed_hosts = os.getenv('ALLOWED_HOSTS')
if raw_allowed_hosts:
    ALLOWED_HOSTS = [h.strip() for h in raw_allowed_hosts.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]'] if DEBUG else DEFAULT_ALLOWED_HOSTS


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'storages',

    'accounts.apps.AccountsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'includoland.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'includoland.wsgi.application'

# DB configuration
db_from_env = os.getenv('DATABASE_URL') or os.getenv('DATABASE_PUBLIC_URL')

if db_from_env:
    ssl_required = not DEBUG
    if '@db:' in db_from_env or 'localhost' in db_from_env or '127.0.0.1' in db_from_env:
        ssl_required = False

    DATABASES = {
        'default': dj_database_url.config(
            default=db_from_env,
            conn_max_age=600,
            ssl_require=ssl_required,
        )
    }

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'uk'
TIME_ZONE = 'Europe/Kyiv'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']


# --- Cloudflare R2 (S3-compatible) for media files ---
# Remote-only: media must never be stored locally.

# Cloudflare R2 bucket details (your values)
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', 'includo-land-storage')
AWS_S3_ENDPOINT_URL = os.getenv(
    'AWS_S3_ENDPOINT_URL',
    'https://80a148f7dc24f9ebadac3a04a7b15c42.r2.cloudflarestorage.com',
)

# Public Development URL (r2.dev) domain WITHOUT scheme
AWS_S3_CUSTOM_DOMAIN = os.getenv(
    'AWS_S3_CUSTOM_DOMAIN',
    'pub-5679526c27734cf1ac685264f79b3fa4.r2.dev',
)

# Credentials (store in .env or platform environment variables)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

if not (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY):
    raise RuntimeError('AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY must be set (remote-only media storage).')

# R2 specifics / sane defaults
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'auto')
AWS_S3_SIGNATURE_VERSION = os.getenv('AWS_S3_SIGNATURE_VERSION', 's3v4')
AWS_S3_ADDRESSING_STYLE = os.getenv('AWS_S3_ADDRESSING_STYLE', 'path')
AWS_S3_USE_SSL = True

# Public read URLs without signed querystrings (r2.dev public bucket)
# False => clean public URLs; True => signed URLs with query params.
AWS_QUERYSTRING_AUTH = os.getenv('AWS_QUERYSTRING_AUTH', '0').lower() in {'1', 'true', 'yes'}

# Avoid ACL calls (often blocked / unsupported depending on bucket settings)
AWS_DEFAULT_ACL = None

# Overwrite behavior.
# Setting this to True avoids a pre-save HeadObject existence check (which can 403 on some R2 API tokens).
# We keep filenames unique via upload_to (UUID) so overwrites are extremely unlikely.
AWS_S3_FILE_OVERWRITE = os.getenv('AWS_S3_FILE_OVERWRITE', '1').lower() in {'1', 'true', 'yes'}

STORAGES = {
    'default': {
        'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"
MEDIA_ROOT = None

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/profile/'
LOGOUT_REDIRECT_URL = '/'

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', '1').lower() not in {'0', 'false', 'no'}
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

DEFAULT_CSRF_TRUSTED_ORIGINS = [
    'https://includolandapp-production.up.railway.app',
]

raw_csrf_trusted = os.getenv('CSRF_TRUSTED_ORIGINS')
if raw_csrf_trusted:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in raw_csrf_trusted.split(',') if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [] if DEBUG else DEFAULT_CSRF_TRUSTED_ORIGINS

