from celery import shared_task
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
    #
    # for connection in active_connections:

