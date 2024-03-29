from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async
import requests
import json
from celery.result import allow_join_result
from tickets.background.vk.upload_file import upload_doc


@shared_task()
def vk_message(message_id):
    from backend.models import TicketMessage, TelegramBot, Attachment
    from backend.serializers import TicketMessageSerializer
    from tickets.settings import SUPPORTBOT
    from django.db import transaction
    print(message_id)
    with transaction.atomic():
        msg = TicketMessage.objects.select_for_update().get(id=message_id)
        uploaded_docs = []
        if Attachment.objects.filter(message=msg).exists():
            str_files = '&attachment='
            for attach in Attachment.objects.filter(message=msg):
                uploaded_docs.append(upload_doc.delay(attach_id=attach.id, platform_id=str(msg.ticket.platform.uuid)))

            for doc in uploaded_docs:
                with allow_join_result():
                    result = doc.wait(timeout=100, interval=0.5)
                    str_files += f'{result["type"]}{result["owner_id"]}_{result["id"]},'
        else:
            str_files = ''

        auth = {
            "Authorization": f"Bearer {msg.ticket.platform.vk_access_key}"
        }

        send_message = requests.get(
                f"https://api.vk.com/method/messages.send?user_id={msg.ticket.tg_user.vk_id}{str_files}&random_id=0&message={msg.message_text}&v=5.199", headers=auth)

        print(send_message.text)

        if send_message.status_code == 200:
            msg.sending_state = 'delivered'
            msg.save()

            channel_layer = get_channel_layer()
            data = {'type': 'message_delivered', 'message': TicketMessageSerializer(msg).data}
            async_to_sync(channel_layer.group_send)("active", {"type": "chat.message",
                                                              "message": json.dumps(data)})
