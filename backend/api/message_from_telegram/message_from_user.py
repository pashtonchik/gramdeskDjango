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
def telegram(request, token):
    data = json.loads(request.body.decode("utf-8"))
    print(data)
    bot = TelegramBots.objects.get(bot_apikey=token)


    users = User.objects.filter(tg_id=data.get('message', {}).get('chat', {}).get('id', "0"), type='client')

    if users.exists():
        cur_user = users.first()
    else:
        cur_user = User(
            type='client',
            tg_id=data.get('message', {}).get('chat', {}).get('id', "Не известно"),
            tg_username=data.get('message', {}).get('chat', {}).get('username', "Не известно"),
        )
        cur_user.save()

    support = bot.user

    tickets = Ticket.objects.select_for_update().filter(tg_user=cur_user, status__in=['created', 'in_progress'], support_user=support)

    if not tickets.exists():
        cur_ticket = Ticket(
            tg_user=cur_user,
            status='created',
            support_user=support,
        )
        cur_ticket.save()
    else:
        cur_ticket = tickets.order_by('-date_created').first()

    if data.get('message', {}).get('text', None):
        new_message = TicketMessage(
            tg_user=cur_user,
            sender='client',
            content_type='text',
            sending_state='sent',
            message_text=data['message'],
            ticket=cur_ticket,
        )
        new_message.save()
    # elif data['content_type'] == 'file':
    #     new_message = TicketMessage(
    #         tg_user=cur_user,
    #         sender='client',
    #         content_type='file',
    #         sending_state='sent',
    #         message_text=data['caption'],
    #         ticket=cur_ticket,
    #     )
    #     new_message.save()
    #
    #     file = request.data['file']
    #     new_message.message_file.save(file.name, file, save=True)
    #     new_message.save()
    #
    #
    #
    #
    channel_layer = get_channel_layer()
    data = {'type': 'new_message', 'message': TicketMessageSerializer(new_message, context={"from_user_type": "client"}).data}
    async_to_sync(channel_layer.group_send)("active", {"type": "chat.message",
                                                  "message": json.dumps(data)})
    json.dumps({
        'file': None,
        'text': data['message'],
        'date': int(new_message.date_created.timestamp())
    })
    return Response(status=status.HTTP_200_OK, data=data)
