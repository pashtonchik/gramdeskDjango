import datetime
import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from backend.models import *


@transaction.atomic()
@api_view(['POST'])
def get_all_tickets(request):
    data = json.loads(request.body.decode("utf-8"))

    date_created = data.get('date_created', None)
    date_closed = data.get('date_closed', None)
    status_tickets = data.get('status', None)
    page = data.get('page', 1)
    default_start_time = datetime.datetime.fromtimestamp(5000000)
    default_end_time = datetime.datetime.now()

    all_tickets = Ticket.objects.all().order_by('-date_created')

    if date_created:
        all_tickets = all_tickets.filter(
            date_created__gte=datetime.datetime.fromtimestamp(date_created[0]) if date_created[
                0] else default_start_time,
            date_created__lte=datetime.datetime.fromtimestamp(date_created[1]) if date_created[1] else default_end_time)

    if date_closed:
        if date_closed[0]:
            all_tickets = all_tickets.filter(
                date_closed__gte=datetime.datetime.fromtimestamp(date_closed[0]) if date_closed[
                    0] else default_start_time)
        if date_closed[1]:
            all_tickets = all_tickets.filter(
                date_closed__lte=datetime.datetime.fromtimestamp(date_closed[1]) if date_closed[
                    1] else default_end_time)

    if status_tickets:
        all_tickets = all_tickets.filter(status__in=status_tickets)

    data = {}
    data['tickets'] = []

    for i in all_tickets[(20 * (page - 1)) : (page * 20)]:
        data['tickets'].append({
            'ticket_id': i.uuid,
            'tickets_user': i.tg_user,
            'status': i.status,
            'date_created': int(i.date_created.timestamp()) if i.date_created else '-',
            'date_closed': int(i.date_closed.timestamp()) if i.date_closed else '-',
        })

    data['ok'] = True
    data['page'] = page
    data['count'] = all_tickets.count()

    return Response(status=status.HTTP_200_OK, data=data)