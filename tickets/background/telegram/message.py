from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async
import requests
import json


@shared_task()
def telegram_message(message_id):
    from backend.models import TicketMessage, TelegramBot
    from backend.serializers import TicketMessageSerializer
    from tickets.settings import SUPPORTBOT

    msg = TicketMessage.objects.get(id=message_id)
    print('отправка сообщения в бот')
    data = {
        "chat_id": msg.tg_user.tg_id,
        "parse_mode": "HTML",
        "text": msg.message_text,
    }

    send_message = requests.get(
        f"https://api.telegram.org/bot{TelegramBot.objects.get(platform=msg.ticket.platform).bot_apikey}/sendMessage", json=data)
    print(send_message.status_code, send_message.text)
    if send_message.status_code != 200:
        send_message = requests.get(
            f"https://api.telegram.org/bot{SUPPORTBOT}/sendMessage", json=data)

    if send_message.status_code == 200:
        msg.sending_state = 'delivered'
        msg.save()

        channel_layer = get_channel_layer()
        data = {'type': 'message_delivered', 'message': TicketMessageSerializer(msg).data}
        async_to_sync(channel_layer.group_send)("active", {"type": "chat.message",
                                                          "message": json.dumps(data)})