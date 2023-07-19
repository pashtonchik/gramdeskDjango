import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from backend.models import *
from backend.serializers import TicketMessageSerializer
from tickets.celery_tasks import send_message_to_client


@transaction.atomic()
@api_view(['POST'])
def new_message(request):
    data = json.loads(request.body.decode("utf-8"))

    users = Client.objects.filter(tg_id=data['tg_id'])
    if Client.objects.filter(tg_id=data['tg_id']).exists():
        cur_user = users.first()
    else:
        cur_user = Client(
            tg_id=data['tg_id'],
            tg_username=data['tg_username']
        )
        cur_user.save()

    tickets = Ticket.objects.select_for_update().filter(tg_user=cur_user, status__in=['created', 'in_progress'])

    if not tickets.exists():
        cur_ticket = Ticket(
            tg_user=cur_user,
            status='created',
        )
        cur_ticket.save()
    else:
        cur_ticket = tickets.order_by('-date_created').first()

    new_message = TicketMessage(
        tg_user=cur_user,
        sender='client',
        content_type='text',
        sending_state='sent',
        message_text=data['message'],
        ticket=cur_ticket,
    )
    new_message.save()

    send_message_to_client.delay(message_id=new_message.id)

    channel_layer = get_channel_layer()

    data = {'type': 'new_message', 'message': TicketMessageSerializer(new_message).data}
    async_to_sync(channel_layer.group_send)("chat1", {"type": "chat.message",
                                                      "message": json.dumps(data)})
    # json.dumps({
    #     'file': None,
    #     'text': data['message'],
    #     'date': int(new_message.date_created.timestamp())
    # })})
    return Response(status=status.HTTP_200_OK, data=data)
