"""HTTP client for Aiverse ML FastAPI service."""
import logging

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


def call_ml_service(endpoint: str, payload: dict, timeout: float = None) -> dict | None:
    base = getattr(settings, "ML_SERVICE_URL", "http://localhost:8001").rstrip("/")
    timeout = timeout or getattr(settings, "ML_SERVICE_TIMEOUT", 3.0)
    try:
        resp = httpx.post(
            f"{base}{endpoint}",
            json=payload,
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )
        if resp.status_code == 200:
            return resp.json()
        logger.warning("ML service %s returned %s", endpoint, resp.status_code)
    except Exception as e:
        logger.warning("ML service call failed: %s", e)
    return None
