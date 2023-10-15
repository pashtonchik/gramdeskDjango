import json


def get_messages(connection, data, from_user_type):
    from backend.models import Ticket, TicketMessage, User
    from backend.serializers import TicketSerializer, TicketMessageSerializer
    chat_id = data['chat_id']
    last_message = data.get('last_message_id', None)

    ticket = Ticket.objects.get(uuid=chat_id)
    last_messages = TicketMessage.objects.filter(ticket=ticket, deleted=False).order_by('-date_created')
    if last_message:
        last_message = last_messages.get(id=last_message)

        message_to_output = last_messages.filter(date_created__lt=last_message.date_created).order_by('-date_created')

    else:
        message_to_output = last_messages.order_by('-date_created')

    output_data = {
        'ok': True,
        'event': 'response_action',
        'action': 'get_messages',
        'total_messages': last_messages.count(),
        'messages': TicketMessageSerializer(message_to_output[:20], many=True,
                                            context={"from_user_type": from_user_type}).data
    }

    connection.send(text_data=json.dumps(output_data))
