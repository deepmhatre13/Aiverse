import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

django_asgi_app = get_asgi_application()

# Import after Django is initialized to avoid AppRegistryNotReady errors
from backend.routing import websocket_urlpatterns
from discussions.middleware import JWTAuthMiddleware

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            JWTAuthMiddleware(AuthMiddlewareStack(URLRouter(websocket_urlpatterns)))
        ),
    }
)