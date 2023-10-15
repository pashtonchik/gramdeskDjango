import json

from django.db import transaction

from tickets.sockets.tools.events.update_message import update_message_by_channel_group


@transaction.atomic()
def update_message_by_support(connection, data, from_user_type):
    from backend.models import Ticket, TicketMessage, User
    from backend.serializers import TicketSerializer, TicketMessageSerializer
    message = data['message']
    cur_message = TicketMessage.objects.select_for_update().get(id=message['id'])

    if message['sending_state'] == 'read' and cur_message.sending_state == 'sent':
        cur_message.sending_state = 'read'
        cur_message.read_by_received = True

    cur_message.save()

    responce_data = {
        'ok': True,
        'event': "response_action",
        'action': "update_message",
        'message': TicketMessageSerializer(cur_message, context={"from_user_type": from_user_type}).data,
    }
    connection.send(text_data=json.dumps(responce_data))

    update_message_by_channel_group('support', 'active_support', message)
    update_message_by_channel_group('client', f'client_{message.tg_user.id}', message)