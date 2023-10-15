import json

from django.db import transaction

from tickets.sockets.tools.events.delete_message import delete_message_by_channel_group


@transaction.atomic()
def delete_message_by_support(connection, data, from_user_type):
    from backend.models import Ticket, TicketMessage, User
    from backend.serializers import TicketSerializer, TicketMessageSerializer
    message = data['message']
    cur_message = TicketMessage.objects.select_for_update().get(id=message['id'])

    if not cur_message.deleted:
        cur_message.deleted = True

        cur_message.save()

        response_data = {
            'ok': True,
            'event': "response_action",
            'action': "delete_message",
            'message': TicketMessageSerializer(cur_message, context={"from_user_type": from_user_type}).data,
        }

        delete_message_by_channel_group('support', 'active_support', message)
        delete_message_by_channel_group('client', f'client_{message.tg_user.id}', message)
    else:
        response_data = {
            'ok': False,
            'event': "response_action",
            'action': "delete_message",
            'error': 'Already deleted',
            'message': TicketMessageSerializer(cur_message, context={"from_user_type": from_user_type}).data,
        }
    connection.send(text_data=json.dumps(response_data))