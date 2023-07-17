from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter

from backend.consumer import LiveScoreConsumer

websockets = URLRouter([
    path("apiapi/<int:game_id>", LiveScoreConsumer),
])