# import os
#
# import django
# from channels.auth import AuthMiddlewareStack
# from channels.security.websocket import AllowedHostsOriginValidator
# from django.conf import settings
#
# from django.core.asgi import get_asgi_application
# from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
# from django.urls import path, re_path
#
# from backend.consumer import LiveScoreConsumer
# from backend.client_consumer import ClientConsumer
# from backend.socket_auth import TokenAuthMiddleware
# from backend.socket_heartbeat import HeartbeatMiddleware
# from tickets.wsgi import *
# # from .wsgi import application
# settings.configure()
import os

import django
from django.core.asgi import get_asgi_application

DJANGO_SETTINGS_MODULE = os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tickets.settings')
django.setup()
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import re_path

from tickets.client_consumer import ClientConsumer
from tickets.consumer import LiveScoreConsumer

from backend.socket_auth import TokenAuthMiddleware



# application = get_asgi_application()

application = ProtocolTypeRouter(TokenAuthMiddleware(
    {
    'http': get_asgi_application(),
    'websocket': AllowedHostsOriginValidator(
        URLRouter(
            [
                re_path("apiapi/", LiveScoreConsumer.as_asgi()),
                re_path("client/", ClientConsumer.as_asgi()),
            ]
        )
    )
}
)
)