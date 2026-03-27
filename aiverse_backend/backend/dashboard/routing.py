from django.urls import re_path
from .consumers import LiveUpdatesConsumer

# Path may include leading slash (ASGI scope path)
websocket_urlpatterns = [
    re_path(r'^/ws/live-updates/(?P<user_id>\d+)/$', LiveUpdatesConsumer.as_asgi()),
    re_path(r'^ws/live-updates/(?P<user_id>\d+)/$', LiveUpdatesConsumer.as_asgi()),
]
