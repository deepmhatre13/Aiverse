"""Custom middleware and logging utilities for request handling."""

import contextvars
import uuid

from django.conf import settings


request_id_ctx = contextvars.ContextVar('request_id', default='-')


def get_request_id():
    """Expose request id for logging filters."""
    return request_id_ctx.get()


class RequestIdLogFilter:
    """Attach request id to every log record."""

    def filter(self, record):
        record.request_id = get_request_id()
        return True


class RequestIdMiddleware:
    """Attach a stable request id to request context and response headers."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        inbound_id = request.headers.get('X-Request-ID')
        req_id = inbound_id or uuid.uuid4().hex
        request.request_id = req_id

        token = request_id_ctx.set(req_id)
        try:
            response = self.get_response(request)
        finally:
            request_id_ctx.reset(token)

        response['X-Request-ID'] = req_id
        return response


class CrossOriginOpenerPolicyMiddleware:
    """
    Set COOP and COEP headers for Google Sign-In popup communication.
    Skips headers if SECURE_CROSS_ORIGIN_OPENER_POLICY is None.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        coop = getattr(settings, 'SECURE_CROSS_ORIGIN_OPENER_POLICY', None)
        if coop is not None:
            response['Cross-Origin-Opener-Policy'] = coop
        
        return response
