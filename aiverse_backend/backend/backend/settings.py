
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
import os
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")


SECRET_KEY = 'django-insecure-qm#yv_e0m7jr^0*a=kuor&#rra2&-1ebnrhn+5xnppncka%$i6'

DEBUG = True

# Frontend URL for OAuth redirects and CORS
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')

CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://localhost:3000',
    'http://localhost:8080',
    'http://127.0.0.1:5173',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:8080',
]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:5173',
    'http://localhost:3000',
    'http://localhost:8080',
    'http://127.0.0.1:5173',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:8080',
]

# CORS with credentials for cookies
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Session and cookie configuration for localhost (no HTTPS)
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'

HF_API_KEY = os.getenv("HF_API_KEY")



INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'ml',
    'users',
    'corsheaders',
    #'rest_framework_simplejwt',
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

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'backend.middleware.RequestIdMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'backend.middleware.CrossOriginOpenerPolicyMiddleware',  
]

# Note: CORS configured with explicit allowed origins above


ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases



# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'aiverse'),
        'USER': os.getenv('POSTGRES_USER', 'aiverse_user'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'StrongPassword123'),
        'HOST': os.getenv('POSTGRES_HOST', '127.0.0.1'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}

REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_URL = os.getenv('REDIS_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/1')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
        'TIMEOUT': 300,
        'OPTIONS': {
            'socket_connect_timeout': 2,
            'socket_timeout': 2,
        },
    }
}


AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'user': '1000/day',
        'anon': '100/day',
        'auth': '20/min',
        'profile': '120/min',
        'playground_train': '10/min',
        'playground_jobs': '30/min',
    },
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ),
}



# =========================
# CELERY CONFIGURATION
# =========================

CELERY_BROKER_URL = "redis://127.0.0.1:6379/0"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/0"

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 1800
CELERY_TASK_SOFT_TIME_LIMIT = 1500
CELERY_TIMEZONE = "UTC"
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_ROUTES = {
    'playground.tasks.run_training_task': {'queue': 'ml_train'},
}


# ============================================================================
# GOOGLE OAUTH CONFIGURATION (Backend-Managed)
# ============================================================================
# OAuth flow:
# 1. Frontend redirects user to /api/auth/google/login/
# 2. Backend redirects to Google
# 3. Google redirects back to /api/auth/google/callback/
# 4. Backend exchanges code for tokens
# 5. Backend creates session/JWT
# 6. Backend redirects to frontend with auth set
# NO frontend-side Google SDK, NO tokens sent to frontend, NO FedCM errors

GOOGLE_OAUTH_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID', '')
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', '')
GOOGLE_OAUTH_REDIRECT_URI = f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/api/auth/google/callback/"

GOOGLE_AUTH_ENDPOINT = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_ENDPOINT = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_ENDPOINT = 'https://www.googleapis.com/oauth2/v2/userinfo'

# ===== SECURITY: Cross-Origin-Opener-Policy =====
# GSI (Google Identity Services) uses postMessage from popup.
# "same-origin-allow-popups" allows GSI popups to post messages back.
# Set COOP_DISABLED=1 in .env to disable (fixes persistent COOP conflicts).
SECURE_CROSS_ORIGIN_OPENER_POLICY = (
    None
    if os.environ.get("COOP_DISABLED", "").lower() in ("1", "true", "yes")
    else "same-origin-allow-popups"
)

# Validate OAuth credentials on startup
if DEBUG:
    if not GOOGLE_OAUTH_CLIENT_ID:
        import warnings
        warnings.warn(
            '[WARN] GOOGLE_OAUTH_CLIENT_ID not configured in .env. '
            'Google OAuth login will not work. '
            'Add to backend/.env: GOOGLE_OAUTH_CLIENT_ID=YOUR_CLIENT_ID.apps.googleusercontent.com'
        )
    else:
        print(f"[OK] GOOGLE_OAUTH_CLIENT_ID configured: {GOOGLE_OAUTH_CLIENT_ID[:20]}...")


GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')  # AIza...

# Stripe Configuration (TEST MODE) - Optional when Razorpay is used
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')  # sk_test_...
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')  # pk_test_...
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')  # whsec_...

# Razorpay Configuration (India) - Optional when Stripe is used
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')

# Media files (for invoice PDFs)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Ensure media directory exists
os.makedirs(MEDIA_ROOT, exist_ok=True)

# Celery Beat Schedule (for daily snapshot generation)
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'generate-daily-snapshots': {
        'task': 'timeline.tasks.generate_daily_snapshots',
        'schedule': crontab(hour=0, minute=5),  # Run at 00:05 daily
    },
    'snapshot-leaderboard-weekly': {
        'task': 'leaderboard.tasks.snapshot_leaderboard',
        'schedule': crontab(minute='*/15'),
        'args': ('weekly', 10000),
    },
    'snapshot-leaderboard-monthly': {
        'task': 'leaderboard.tasks.snapshot_leaderboard',
        'schedule': crontab(minute='*/15'),
        'args': ('monthly', 10000),
    },
    'snapshot-leaderboard-alltime': {
        'task': 'leaderboard.tasks.snapshot_leaderboard',
        'schedule': crontab(minute='*/15'),
        'args': ('alltime', 10000),
    },
}


ASGI_APPLICATION = 'backend.asgi.application'

# Channels Layer Configuration (Redis backend)
# Run Redis: redis-server (default 127.0.0.1:6379)
# Use daphne backend.asgi:application (not runserver) for WebSocket support
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(
                os.environ.get("REDIS_HOST", "127.0.0.1"),
                int(os.environ.get("REDIS_PORT", 6379)),
            )],
        },
    },
}

DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50 MB

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'request_id': {
            '()': 'backend.middleware.RequestIdLogFilter',
        },
    },
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'filters': ['request_id'],
            'formatter': 'standard',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Default auto field for models
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Environment validation
def validate_environment():
    """Validate required environment variables at startup. Crashes server if missing."""
    missing_vars = []

    # GEMINI_API_KEY is always required (for Mentor)
    if not GEMINI_API_KEY or not isinstance(GEMINI_API_KEY, str) or GEMINI_API_KEY.strip() == '':
        missing_vars.append('GEMINI_API_KEY')

    # At least one payment gateway for paid courses (Stripe OR Razorpay)
    stripe_ok = STRIPE_SECRET_KEY and isinstance(STRIPE_SECRET_KEY, str) and STRIPE_SECRET_KEY.strip() != ''
    razorpay_key_id = os.environ.get('RAZORPAY_KEY_ID', '')
    razorpay_key_secret = os.environ.get('RAZORPAY_KEY_SECRET', '')
    razorpay_ok = (
        razorpay_key_id and razorpay_key_secret and
        isinstance(razorpay_key_id, str) and razorpay_key_id.strip() != '' and
        isinstance(razorpay_key_secret, str) and razorpay_key_secret.strip() != ''
    )
    if not stripe_ok and not razorpay_ok and not missing_vars:
        # Only warn; allow server to start (free courses still work)
        import warnings
        warnings.warn(
            '[WARN] No payment gateway configured. Add STRIPE_SECRET_KEY or RAZORPAY_KEY_ID+RAZORPAY_KEY_SECRET to .env for paid course purchases.'
        )

    if missing_vars:
        raise ValueError(
            f"CRITICAL: Missing required environment variables: {', '.join(missing_vars)}. "
            f"Server cannot start without these. Check your .env file."
        )

    # Validate Gemini API key format (basic check)
    if GEMINI_API_KEY and not GEMINI_API_KEY.startswith('AIza'):
        raise ValueError(
            f"CRITICAL: GEMINI_API_KEY appears invalid. "
            f"Google Gemini API keys must start with 'AIza'. "
            f"Check your .env file."
        )

    # Validate Stripe key format (basic check) - only if Stripe is used
    if stripe_ok and not STRIPE_SECRET_KEY.startswith('sk_'):
        raise ValueError(
            f"CRITICAL: STRIPE_SECRET_KEY appears invalid. "
            f"Stripe secret keys must start with 'sk_'. "
            f"Check your .env file."
        )


# Validate environment on import (at server startup)
validate_environment()