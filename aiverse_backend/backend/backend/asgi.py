"""
ASGI config for Django Channels support.

Run with: daphne backend.asgi:application (not runserver for WebSocket)
"""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

django_asgi_app = get_asgi_application()

from discussions.routing import websocket_urlpatterns as discussion_ws
from dashboard.routing import websocket_urlpatterns as dashboard_ws
from playground.routing import websocket_urlpatterns as playground_ws
from discussions.middleware import JWTAuthMiddleware

all_websocket_urlpatterns = discussion_ws + dashboard_ws + playground_ws

# JWT first (token in query ?token=...), then AuthMiddlewareStack for session
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            AuthMiddlewareStack(URLRouter(all_websocket_urlpatterns))
        )
    ),
})