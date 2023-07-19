import requests

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
        "text": msg.text,
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







