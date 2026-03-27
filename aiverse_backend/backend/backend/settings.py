import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ======================
# CORE
# ======================

SECRET_KEY = os.environ["SECRET_KEY"]  # must exist

DEBUG = os.environ.get("DEBUG", "False") == "True"

ALLOWED_HOSTS = ["*"]

# ======================
# APPS
# ======================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'corsheaders',
    'rest_framework',

    'ml',
    'users',
    'learn',
    'mentor',
    'dashboard',
    'timeline',
    'leaderboard',
    'discussions',
    'channels',
    'live',
    'tracks',
    'playground',
    'problems',
    'submissions',
]

# ======================
# MIDDLEWARE
# ======================

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ======================
# URL
# ======================

ROOT_URLCONF = 'backend.urls'
WSGI_APPLICATION = 'backend.wsgi.application'
ASGI_APPLICATION = 'backend.asgi.application'

# ======================
# DATABASE (RENDER)
# ======================

DATABASES = {
    'default': dj_database_url.config(conn_max_age=600)
}

# ======================
# STATIC
# ======================

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# ======================
# MEDIA
# ======================

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ======================
# REDIS
# ======================

REDIS_URL = os.environ["REDIS_URL"]

# ======================
# CACHE
# ======================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

# ======================
# CELERY
# ======================

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

# ======================
# CHANNELS
# ======================

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    },
}

# ======================
# CORS
# ======================

CORS_ALLOW_ALL_ORIGINS = True

# ======================
# AUTH
# ======================

AUTH_USER_MODEL = 'users.User'

# ======================
# REST
# ======================

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ]
}

# ======================
# TIME
# ======================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
HF_API_KEY = os.environ.get("HF_API_KEY")

GOOGLE_OAUTH_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")