import os
from pathlib import Path
from urllib.parse import urlparse

import dj_database_url
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
DEBUG = env_bool("DEBUG", False)
IS_PRODUCTION = env_bool("IS_PRODUCTION", not DEBUG)

if IS_PRODUCTION and SECRET_KEY == "dev-secret-key":
    raise ImproperlyConfigured("SECRET_KEY must be set in production")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if render_host and render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_host)

if IS_PRODUCTION and not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS must be set in production")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "channels",
    "ml",
    "users",
    "learn",
    "mentor",
    "dashboard",
    "timeline",
    "leaderboard",
    "discussions",
    "live",
    "tracks",
    "playground",
    "problems",
    "submissions",
    "intelligence.apps.IntelligenceConfig",
    # NEW - Event tracking and learning analytics
    "tracking",
    "learner",
    "recommendations",
    "analytics",
    "notifications",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"
WSGI_APPLICATION = "backend.wsgi.application"
ASGI_APPLICATION = "backend.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5432/aiverse")

db_ssl_override = os.getenv("DB_SSL_REQUIRE")
if db_ssl_override is not None:
    db_ssl_require = env_bool("DB_SSL_REQUIRE", False)
else:
    parsed_db_url = urlparse(DATABASE_URL)
    db_host = (parsed_db_url.hostname or "").lower()
    is_local_db_host = db_host in {"localhost", "127.0.0.1", "::1"}
    db_ssl_require = IS_PRODUCTION and not is_local_db_host

DATABASES = {
    "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=db_ssl_require)
}

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    }
}

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Kolkata"
CELERY_TASK_DEFAULT_QUEUE = os.getenv("CELERY_DEFAULT_QUEUE", "default")
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_RESULT_EXPIRES = 60 * 60 * 24
CELERY_TASK_ROUTES = {
    "mentor.run_mentor_task": {
        "queue": CELERY_TASK_DEFAULT_QUEUE,
    }
}

# Celery Beat Schedule for recurring tasks
from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    'generate-daily-recommendations': {
        'task': 'tracking.tasks.generate_daily_recommendations_for_all',
        'schedule': crontab(hour=2, minute=0),
    },
    'update-dropout-risk-all-users': {
        'task': 'tracking.tasks.update_dropout_risk_all_users',
        'schedule': crontab(hour=2, minute=0),
    },
    'recompute-mastery-6h': {
        'task': 'tracking.tasks.recompute_all_mastery_scores',
        'schedule': crontab(minute=0, hour='*/6'),
    },
    'retrain-ml-models': {
        'task': 'tracking.tasks.retrain_ml_models_nightly',
        'schedule': crontab(hour=2, minute=30),
    },
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "auth": "10/min",
        "anon": "100/hour",
        "user": "60/hour",
        "profile": "60/hour",
        "playground_train": "30/hour",
        "playground_jobs": "120/hour",
    }
}

SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("Bearer",),
}

AUTH_USER_MODEL = "users.User"

if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "")
    CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "")
else:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")
    CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")
    
    if not CORS_ALLOWED_ORIGINS:
        raise ImproperlyConfigured("CORS_ALLOWED_ORIGINS must be set in production")
    if not CSRF_TRUSTED_ORIGINS:
        raise ImproperlyConfigured("CSRF_TRUSTED_ORIGINS must be set in production")

PRODUCTION_FRONTEND_ORIGIN = "https://aiverse-pink.vercel.app"
if PRODUCTION_FRONTEND_ORIGIN not in CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS.append(PRODUCTION_FRONTEND_ORIGIN)
if PRODUCTION_FRONTEND_ORIGIN not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(PRODUCTION_FRONTEND_ORIGIN)

CORS_ALLOW_CREDENTIALS = True

if IS_PRODUCTION:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
    SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", True)
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
else:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False

SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
CSRF_COOKIE_SAMESITE = os.getenv("CSRF_COOKIE_SAMESITE", "Lax")

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Cross-Origin policies
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"  # Allow Google OAuth popup communication

default_stripe_mode = "live" if IS_PRODUCTION else "test"
STRIPE_MODE = os.getenv("STRIPE_MODE", default_stripe_mode).strip().lower()

STRIPE_TEST_SECRET_KEY = os.getenv("STRIPE_TEST_SECRET_KEY")
STRIPE_TEST_PUBLISHABLE_KEY = os.getenv("STRIPE_TEST_PUBLISHABLE_KEY")
STRIPE_TEST_WEBHOOK_SECRET = os.getenv("STRIPE_TEST_WEBHOOK_SECRET")

STRIPE_LIVE_SECRET_KEY = os.getenv("STRIPE_LIVE_SECRET_KEY")
STRIPE_LIVE_PUBLISHABLE_KEY = os.getenv("STRIPE_LIVE_PUBLISHABLE_KEY")
STRIPE_LIVE_WEBHOOK_SECRET = os.getenv("STRIPE_LIVE_WEBHOOK_SECRET")

if STRIPE_MODE == "live":
    STRIPE_SECRET_KEY = STRIPE_LIVE_SECRET_KEY or os.getenv("STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY = STRIPE_LIVE_PUBLISHABLE_KEY or os.getenv("STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET = STRIPE_LIVE_WEBHOOK_SECRET or os.getenv("STRIPE_WEBHOOK_SECRET")
else:
    STRIPE_SECRET_KEY = STRIPE_TEST_SECRET_KEY or os.getenv("STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY = STRIPE_TEST_PUBLISHABLE_KEY or os.getenv("STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET = STRIPE_TEST_WEBHOOK_SECRET or os.getenv("STRIPE_WEBHOOK_SECRET")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")

# ML recommendation service
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://localhost:8001")
ML_SERVICE_TIMEOUT = float(os.getenv("ML_SERVICE_TIMEOUT", "3.0"))
ML_INTERNAL_KEY = os.getenv("ML_INTERNAL_KEY", "aiverse_ml_internal_key")

# Google OAuth Configuration
GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_OAUTH_REDIRECT_URI = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "")

# ==============================
# LOGGING CONFIGURATION
# ==============================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'users': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'recommendations': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'learner': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'tracking': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    }
}
