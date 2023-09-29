from django.urls import path
from channels.routing import URLRouter

from tickets.consumer import LiveScoreConsumer

websockets = URLRouter([
    path("apiapi/<int:game_id>", LiveScoreConsumer),
])