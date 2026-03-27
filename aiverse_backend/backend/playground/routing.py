from django.urls import re_path

from .consumers import PlaygroundTrainingConsumer

websocket_urlpatterns = [
    re_path(r"^/ws/playground/(?P<experiment_id>\d+)/$", PlaygroundTrainingConsumer.as_asgi()),
    re_path(r"^ws/playground/(?P<experiment_id>\d+)/$", PlaygroundTrainingConsumer.as_asgi()),
]

