from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async
import requests
import json

from backend.models import Attachment


@shared_task()
def get_file(message_id, telegram_data):
    from backend.models import TicketMessage, TelegramBot
    from backend.serializers import TicketMessageSerializer
    from tickets.settings import SUPPORTBOT
    from django.db import transaction
    print(message_id)
    with transaction.atomic():

        cur_message = TicketMessage.objects.select_for_update().get(id=message_id)
        if not telegram_data.get("message", {}).get("media_group_id", None) and telegram_data.get("message", {}).get("document", None):
            new_file = Attachment(
                message=cur_message,
                name=telegram_data["message"]["document"]["file_name"].split('.')[:-1],
                total_bytes=int(telegram_data["message"]["document"]["file_size"]),
                ext=telegram_data["message"]["document"]["file_name"].split('.')[-1],
                buf_size=500_000,
                telegram_file_id=telegram_data["message"]["document"]["file_id"]
            )
            new_file.save()

            get_file_path = requests.get(f"https://api.telegram.org/bot{TelegramBot.objects.get(platform=new_file.message.ticket.platform).bot_apikey}/getFile?file_id={new_file.telegram_file_id}")
            if get_file_path.status_code == 200:
                data = get_file_path.json()
                new_file.telegram_file_path = data['result']['file_path']
            else:
                raise KeyError
        else:
            media_group_id = telegram_data.get("message", {}).get("media_group_id", None)