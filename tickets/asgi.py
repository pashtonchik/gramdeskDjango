import os
import django


# settings.configure()
DJANGO_SETTINGS_MODULE = os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tickets.settings')
django.setup()
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path
from tickets.client_consumer import ClientConsumer
from tickets.download_consumer import DownloadConsumer
from tickets.consumer import LiveScoreConsumer
from backend.socket_auth import TokenAuthMiddleware
from django.core.asgi import get_asgi_application
from tickets.upload_cunsumer import UploadConsumer



# application = get_asgi_application()

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AllowedHostsOriginValidator(
        TokenAuthMiddleware(
            URLRouter(
                [
                    path("support/<str:jwt>/", LiveScoreConsumer.as_asgi()),
                    path("client/", ClientConsumer.as_asgi()),
                    path("upload/<str:jwt>/", UploadConsumer.as_asgi()),
                    path("download/", DownloadConsumer.as_asgi()),
                ]
            )
        )
    )
})