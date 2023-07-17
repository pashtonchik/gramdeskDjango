import os

import django
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
from django.urls import path, re_path

from backend.consumer import LiveScoreConsumer
# from .wsgi import application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tickets.settings')


# application = get_asgi_application()


application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket':
        URLRouter(
            [
                re_path("apiapi/", LiveScoreConsumer.as_asgi()),
            ]
        )
})