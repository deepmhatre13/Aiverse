"""
System health check endpoint for infrastructure verification.
GET /api/health/
"""
import os
import time

from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET


@method_decorator([csrf_exempt, require_GET], name="dispatch")
class HealthCheckView(View):
    """Returns status and latency metrics for API, DB, and Redis."""

    def get(self, request):
        started = time.perf_counter()

        db_ok, db_ping_ms = _check_database()
        redis_ok, redis_ping_ms = _check_redis()
        channels_ok = _check_channels()

        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        all_ok = redis_ok and db_ok and channels_ok

        from django.conf import settings
        return JsonResponse(
            {
                "status": "ok" if all_ok else "degraded",
                "latency_ms": latency_ms,
                "db_ping_ms": db_ping_ms,
                "redis_ping_ms": redis_ping_ms,
                "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                "version": os.environ.get('APP_VERSION', getattr(settings, 'APP_VERSION', 'dev')),
                "database": db_ok,
                "redis": redis_ok,
                "channels": channels_ok,
            },
            status=200,
        )


def _check_redis():
    try:
        started = time.perf_counter()
        import redis
        from django.conf import settings
        cfg = settings.CHANNEL_LAYERS.get("default", {}).get("CONFIG", {})
        hosts = cfg.get("hosts", [("127.0.0.1", 6379)])
        entry = hosts[0] if hosts else ("127.0.0.1", 6379)
        host, port = entry[0], entry[1] if len(entry) > 1 else 6379
        r = redis.Redis(host=str(host), port=int(port), db=0, socket_connect_timeout=2)
        r.ping()
        return True, round((time.perf_counter() - started) * 1000, 2)
    except Exception:
        return False, None


def _check_database():
    try:
        started = time.perf_counter()
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        return True, round((time.perf_counter() - started) * 1000, 2)
    except Exception:
        return False, None


def _check_channels():
    """Verify Django Channels layer is available."""
    try:
        from channels.layers import get_channel_layer
        layer = get_channel_layer()
        return layer is not None
    except Exception:
        return False
