from django.urls import re_path
from .consumers import ChatWebSocket

websocket_urlpatterns = [
    re_path('^ws/chat/$', ChatWebSocket.as_asgi()),
]