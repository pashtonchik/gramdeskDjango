import os
import django
from django.conf import settings
from django.core.wsgi import get_wsgi_application

# settings.configure()
DJANGO_SETTINGS_MODULE = os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tickets.settings')
django.setup()
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import re_path
from tickets.client_consumer import ClientConsumer
from tickets.consumer import LiveScoreConsumer
from backend.socket_auth import TokenAuthMiddleware
from django.core.asgi import get_asgi_application
from tickets.upload_cunsumer import UploadConsumer



# application = get_asgi_application()

application = ProtocolTypeRouter({
    'http': get_wsgi_application(),
    'websocket': AllowedHostsOriginValidator(
        TokenAuthMiddleware(
            URLRouter(
                [
                    re_path("support/", LiveScoreConsumer.as_asgi()),
                    re_path("client/", ClientConsumer.as_asgi()),
                    re_path("upload/", UploadConsumer.as_asgi()),
                ]
            )
        )
    )
})