from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.db import transaction
import requests


def trade_dispenser_connector():
    trade_dispenser.delay()

@shared_task()
def trade_dispenser():
    from backend.models import SocketConnection
    active_connections = SocketConnection.objects.filter(active=True)
    if not active_connections.exists():
        return "connections dont exist"
    channel_layer = get_channel_layer()
    for connection in active_connections:
        async_to_sync(channel_layer.send)(connection.channel_name, {"chat.message": "123", "text": 'Hey!'})


