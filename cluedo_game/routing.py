from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/session/(?P<session_code>\w+)/$', consumers.SessionConsumer.as_asgi()),
    re_path(r'ws/general/$', consumers.GeneralConsumer.as_asgi()),
]
