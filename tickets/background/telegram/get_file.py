import base64
import datetime

from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async
import requests
import json

from backend.models import Attachment
from tickets.background.telegram_bots.activate_webhook import send_message_read_messages


@shared_task()
def get_file(message_id, telegram_data, is_new_ticket):
    from backend.models import TicketMessage, TelegramBot, Ticket
    from django.db import transaction
    from django.core.files.base import ContentFile
    from backend.serializers import TicketMessageSerializer, TicketSerializer
    print(message_id)
    with transaction.atomic():

        cur_message = TicketMessage.objects.select_for_update().get(id=message_id)
        cur_ticket = Ticket.objects.select_for_update().get(uuid=cur_message.ticket.uuid)


        if telegram_data.get("message", {}).get("document", None) or telegram_data.get("message", {}).get("photo", None):
            if telegram_data.get("message", {}).get("document", None):
                new_file = Attachment(
                    message=cur_message,
                    name=''.join(telegram_data["message"]["document"]["file_name"].split('.')[:-1]),
                    total_bytes=int(telegram_data["message"]["document"]["file_size"]),
                    ext=telegram_data["message"]["document"]["file_name"].split('.')[-1],
                    buf_size=500_000,
                    telegram_file_id=telegram_data["message"]["document"]["file_id"]
                )
            else:
                new_file = Attachment(
                    message=cur_message,
                    name=telegram_data["message"]["photo"][0]["file_unique_id"],
                    total_bytes=int(telegram_data["message"]["photo"][0]["file_size"]),
                    ext='jpeg',
                    buf_size=500_000,
                    telegram_file_id=telegram_data["message"]["photo"][0]["file_id"]
                )
            new_file.save()
            bot_apikey = TelegramBot.objects.get(platform=new_file.message.ticket.platform).bot_apikey
            get_file_path = requests.get(f"https://api.telegram.org/bot{bot_apikey}/getFile?file_id={new_file.telegram_file_id}")
            if get_file_path.status_code == 200:
                data = get_file_path.json()
                new_file.telegram_file_path = data['result']['file_path']
                new_file.save()
            else:
                raise KeyError

            download_file = requests.get(f"https://api.telegram.org/file/bot{bot_apikey}/{new_file.telegram_file_path}")
            if download_file.status_code == 200:
                new_file.file.save(name=new_file.name + '.' + new_file.ext,
                                        content=ContentFile(download_file.content),
                                        save=True)
                new_file.received_bytes = new_file.total_bytes
                new_file.save()

                cur_message.sending_state = 'sent'
                cur_message.save()

                channel_layer = get_channel_layer()

                data = {
                    'event': "incoming",
                    'type': 'new_message',
                    'message': TicketMessageSerializer(cur_message, context={"from_user_type": "support"}).data
                }

                if is_new_ticket:
                    data["new_ticket"] = TicketSerializer(cur_message.ticket, context={"from_user_type": "support"}).data

                cur_ticket.date_last_message = datetime.datetime.now()
                cur_ticket.save()

                async_to_sync(channel_layer.group_send)("active_support", {"type": "chat.message",
                                                                           "message": json.dumps(data)})
                cur_message.sending_state = 'delivered'
                cur_message.save()

                unread_messages = TicketMessage.objects.select_for_update().filter(sending_state="delivered",
                                                                                   sender="support")
                array = [*unread_messages.values_list('id', flat=True)]
                unread_messages.update(sending_state="read", read_by_received=True)

                send_message_read_messages.delay(array, "support")

            else:
                raise KeyError

        else:
            media_group_id = telegram_data.get("message", {}).get("media_group_id", None)