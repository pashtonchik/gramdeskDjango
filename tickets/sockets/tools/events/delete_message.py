import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def delete_message_by_channel_group(to_user_type, channel_group, message):
    from backend.serializers import TicketMessageSerializer
    output_data = {
        'event': 'incoming',
        'type': 'delete_message',
        'message': TicketMessageSerializer(message, context={"from_user_type": to_user_type}).data,
    }

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(channel_group, {"type": "chat.message",
                                                               "message": json.dumps(output_data)})