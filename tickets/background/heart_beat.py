import datetime

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.db import transaction
import requests


def heart_beat_connector():
    heart_beat.delay()

@shared_task()
def heart_beat():
    from backend.models import SocketConnection
    active_connections = SocketConnection.objects.filter(active=True)
    if not active_connections.exists():
        return "connections dont exist"
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)("active_connections", {"type": "chat.message",
                                                  "message": "heartbeat"})

    active_connections.update(last_heartbeat=datetime.datetime.now().timestamp(), approve_heartbeat=False)


