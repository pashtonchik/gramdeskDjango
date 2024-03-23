import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from backend.models import *
from backend.serializers import TicketMessageSerializer, TicketSerializer
from tickets.celery_tasks import send_message_to_client


@transaction.atomic()
@api_view(['POST'])
def telegram(request, token):
    data = json.loads(request.body.decode("utf-8"))
    print(data)
    bot = TelegramBot.objects.get(bot_apikey=token)


    users = User.objects.filter(tg_id=data.get('message', {}).get('chat', {}).get('id', "0"), type='client')

    if users.exists():
        cur_user = users.first()
        if cur_user.is_blocked:
            return Response(status=status.HTTP_200_OK, data={"ok": True})

    else:
        cur_user = User(
            username=data.get('message', {}).get('chat', {}).get('username', f"Telegram User {User.objects.all().count() + 1}"),
            type='client',
            source='telegram',
            tg_id=data.get('message', {}).get('chat', {}).get('id', "Не известно"),
            tg_username=data.get('message', {}).get('chat', {}).get('username', "Не известно"),
        )
        cur_user.save()


    tickets = Ticket.objects.select_for_update().filter(tg_user=cur_user, status__in=['created', 'in_progress'], platform=bot.platform)

    if not tickets.exists():
        cur_ticket = Ticket(
            source='telegram',
            platform=bot.platform,
            tg_user=cur_user,
            status='created',
        )
        cur_ticket.save()
        is_new_ticket = True
    else:
        cur_ticket = tickets.order_by('-date_created').first()
        is_new_ticket = False

    if data.get('message', {}).get('text', None):
        new_message = TicketMessage(
            tg_user=cur_user,
            sender='client',
            content_type='text',
            sending_state='sent',
            message_text=data['message']['text'],
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


    data = {
        'event': "incoming",
        'type': 'new_message',
        'message': TicketMessageSerializer(new_message, context={"from_user_type": "support"}).data
    }

    if is_new_ticket:
        data["new_ticket"] = TicketSerializer(cur_ticket, context={"from_user_type": "support"}).data

    async_to_sync(channel_layer.group_send)("active_support", {"type": "chat.message",
                                                  "message": json.dumps(data)})
    new_message.sending_state = 'delivered'
    new_message.save()

    TicketMessage.objects.select_for_update().filter(sending_state="delivered").update(sending_state="read", read_by_received=True)

    # json.dumps({
    #     'file': None,
    #     'text': data['message'],
    #     'date': int(new_message.date_created.timestamp())
    # })
    return Response(status=status.HTTP_200_OK, data=data)
