from django.urls import re_path

from backend.consumers import TestWebSocketConsumer
from dashboard.routing import websocket_urlpatterns as dashboard_websocket_urlpatterns
from discussions.routing import websocket_urlpatterns as discussions_websocket_urlpatterns
from playground.routing import websocket_urlpatterns as playground_websocket_urlpatterns

websocket_urlpatterns = [
    re_path(r"^ws/test/$", TestWebSocketConsumer.as_asgi()),
] + dashboard_websocket_urlpatterns + discussions_websocket_urlpatterns + playground_websocket_urlpatterns