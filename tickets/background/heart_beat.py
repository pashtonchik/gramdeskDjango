import datetime

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.db import transaction
import requests

from backend.client_consumer import ClientConsumer


def heart_beat_connector():
    heart_beat.delay()


@shared_task()
def heart_beat():
    from backend.models import SocketConnection
    active_connections = SocketConnection.objects.filter(active=True)

    channel_layer = get_channel_layer()

    for connection in active_connections.filter(approve_heartbeat=False, last_heartbeat__gt=0):

        print(connection)

        async_to_sync(channel_layer.group_discard)("active_connections", connection.channel_name)
        async_to_sync(channel_layer.group_discard)(f'client_{connection.user.id}', connection.channel_name)
        consumer = ClientConsumer()

        consumer.disconnect(400)



    if not active_connections.exists():
        return "connections dont exist"
    async_to_sync(channel_layer.group_send)("active_connections", {"type": "chat.message",
                                                  "message": "heartbeat"})

    active_connections.update(last_heartbeat=datetime.datetime.now().timestamp(), approve_heartbeat=False)


