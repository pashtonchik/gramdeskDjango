import json
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async


@shared_task()
def send_message_read_messages(ids_array):
    from backend.models import TicketMessage
    from backend.serializers import TicketMessageSerializer
    messages = TicketMessage.objects.filter(id__in=ids_array)

    for message in messages:

        data = {
            'event': 'incoming',
            'type': 'update_message',
            'ok': True,
            'message': TicketMessageSerializer(message, context={"from_user_type": message.sender}).data,
        }

        channel_layer = get_channel_layer()
        if message.sender == "support":
            async_to_sync(channel_layer.group_send)(f"support_{str(message.ticket.platform.uuid)}", {"type": "chat.message",
                                                                   "message": json.dumps(data)})
        else:
            async_to_sync(channel_layer.group_send)(f"client_{message.tg_user.id}", {"type": "chat.message",
                                                                                     "message": json.dumps(data)})

