import json

import requests
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from backend.serializers import TicketMessageSerializer
from tickets.celery import app
from tickets.settings import SUPPORTBOT


@app.task
def send_message_to_client(message_id):
    from backend.models import TicketMessage

    msg = TicketMessage.objects.get(id=message_id)
    print('отправка сообщения в бот')
    data = {
        "chat_id": msg.tg_user.tg_id,
        "parse_mode": "HTML",
        "text": msg.message_text,
    }

    send_message = requests.get(
        f"https://api.telegram.org/bot{SUPPORTBOT}/sendMessage", json=data)
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







