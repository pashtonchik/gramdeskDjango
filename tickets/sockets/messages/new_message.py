import datetime
import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction

from tickets.sockets.tools.events.new_message import new_message_by_channel_group


@transaction.atomic()
def new_message_to_client(connection, data, from_user_type):
    from backend.models import Ticket, TicketMessage, User, Attachment
    from backend.serializers import TicketSerializer, TicketMessageSerializer
    new_message = data['message']
    ticket = Ticket.objects.select_for_update().get(uuid=new_message['chat_id'])

    message = TicketMessage(
        tg_user=ticket.tg_user,
        employee=User.objects.all().first(),
        sender=from_user_type,
        content_type='text',
        sending_state='sent',
        message_text=new_message['content'],
        ticket=ticket,
    )

    if 'message_to_reply' in new_message:
        if new_message['message_to_reply']:
            message.message_to_reply = TicketMessage.objects.get(id=new_message['message_to_reply']['id'],
                                                                 ticket=message.ticket)

    if 'media' in new_message:
        if new_message['media']:
            message.sending_state = 'uploading_attachments'
            message.save()
            for file in new_message['media']:
                Attachment(
                    message=message,
                    name=file['name'],
                    total_bytes=file['total_size'],
                    ext=file['ext'],
                    buf_size=500_000,
                ).save()
        else:
            message.save()
    else:
        message.save()

    responce_data = {
        'ok': True,
        'event': "response_action",
        'action': "send_message",
        'message': TicketMessageSerializer(message, contexесt={"from_user_type": from_user_type}).data,
    }
    connection.send(text_data=json.dumps(responce_data))

    if message.sending_state == 'sent':
        new_message_by_channel_group('support', f"support_{str(message.ticket.platform.uuid)}", message)
        new_message_by_channel_group('client', f'client_{message.tg_user.id}', message)
    ticket.date_last_message = datetime.datetime.now()
    ticket.save()