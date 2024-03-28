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
def get_file(message_id, vk_data, is_new_ticket):
    from backend.models import TicketMessage, TelegramBot, Ticket
    from django.db import transaction
    from django.core.files.base import ContentFile
    from backend.serializers import TicketMessageSerializer, TicketSerializer
    print(message_id)
    with transaction.atomic():

        cur_message = TicketMessage.objects.select_for_update().get(id=message_id)
        cur_ticket = Ticket.objects.select_for_update().get(uuid=cur_message.ticket.uuid)
        print(vk_data)

        if vk_data.get("object", {}).get("message", {}).get("attachments", []) != []:
            if vk_data.get("object", {}).get("message", {}).get("attachments", [])[-1]:
                attachment = vk_data.get("object", {}).get("message", {}).get("attachments", [])[-1]
                new_file = Attachment(
                    message=cur_message,
                    name=attachment["photo"]["sizes"][-1]["url"].split("impq/")[1].split(".")[0],
                    total_bytes=1,
                    ext=attachment["photo"]["sizes"][-1]["url"].split("impq/")[1].split(".")[1].split("?"),
                    buf_size=500_000,
                    vk_file_url=attachment["photo"]["sizes"][-1]["url"],
                )

            new_file.save()

            download_file = requests.get(new_file.vk_file_url)
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

                async_to_sync(channel_layer.group_send)(f"support_{str(cur_ticket.platform.uuid)}", {"type": "chat.message",
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