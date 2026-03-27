from django.urls import re_path
from .consumers import DiscussionConsumer

# Path may include leading slash (ASGI scope path)
websocket_urlpatterns = [
    re_path(r'^/ws/discussions/(?P<thread_id>\d+)/$', DiscussionConsumer.as_asgi()),
    re_path(r'^ws/discussions/(?P<thread_id>\d+)/$', DiscussionConsumer.as_asgi()),
]