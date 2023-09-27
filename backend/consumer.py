# Встроенные импорты.
import json

from asgiref.sync import async_to_sync, sync_to_async
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
# Импорты сторонних библиотек.
from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from channels.layers import get_channel_layer

# Импорты Django.
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import AnonymousUser

from backend.models import Ticket, TicketMessage, User
from backend.serializers import TicketSerializer, TicketMessageSerializer
from tickets.celery_tasks.send_message_to_client import send_message_to_client
from django.db import transaction


class LiveScoreConsumer(WebsocketConsumer):


    def connect(self):
        async_to_sync(self.channel_layer.group_add)("active_support", self.channel_name)
        async_to_sync(self.channel_layer.group_add)(f'active_connections', self.channel_name)
        print(self.channel_name)

        tickets = Ticket.objects.all()

        new_tickets = tickets.filter(status='created')[:20]
        in_progress_tickets = tickets.filter(status='in_progress')[:20]
        # closed_tickets = tickets.filter(status='closed')[:20]

        data = {}
        data['type'] = 'tickets'
        data['new_tickets'] = TicketSerializer(new_tickets, many=True).data
        data['in_progress_tickets'] = TicketSerializer(in_progress_tickets, many=True).data
        data['ok'] = True

        self.accept()
        self.send(json.dumps(data))


    def disconnect(self, close_code):
        pass

    def open_chat(self, data):
        chat_id = data['chat_id']

        ticket = Ticket.objects.get(uuid=chat_id)
        client = ticket.tg_user
        last_messages = TicketMessage.objects.filter(ticket=ticket).order_by('-date_created')

        unread_message = last_messages.filter(read_by_received=False)
        unread_message.update(read_by_received=True)

        output_data = {}
        output_data['event'] = 'response_action'
        output_data['action'] = 'open_chat'
        output_data['ok'] = True
        output_data['chat_id'] = chat_id
        output_data['total_messages'] = last_messages.count()
        # output_data['client'] = ClientSerializer(client).data
        output_data['messages'] = TicketMessageSerializer(last_messages[:20], many=True).data
        self.send(text_data=json.dumps(output_data))

    def get_messages(self, data):
        chat_id = data['chat_id']
        last_message = data.get('last_message_id', None)

        ticket = Ticket.objects.get(uuid=chat_id)
        last_messages = TicketMessage.objects.filter(ticket=ticket).order_by('-date_created')
        if last_message:
            last_message = last_messages.get(id=last_message)


            message_to_output = last_messages.filter(date_created__lt=last_message.date_created).order_by('-date_created')

        else:
            message_to_output = last_messages.order_by('-date_created')


        output_data = {}
        output_data['event'] = 'response_action'
        output_data['action'] = 'get_messages'
        output_data['ok'] = True
        output_data['total_messages'] = last_messages.count()
        output_data['messages'] = TicketMessageSerializer(message_to_output[:20], many=True).data
        self.send(text_data=json.dumps(output_data))

    @transaction.atomic()
    def new_message_to_client(self, data):
        new_message = data['message']
        ticket = Ticket.objects.select_for_update().get(uuid=new_message['chat_id'])

        message = TicketMessage(
            tg_user=ticket.tg_user,
            employee=User.objects.all().first(),
            sender='employee',
            content_type='text',
            sending_state='sent',
            message_text=new_message['content'],
            ticket=ticket,
        )


        responce_data = {
            'event': "response_action",
            'action': "send_message",
            'message': TicketMessageSerializer(message).data,
        }
        self.send(text_data=json.dumps(responce_data))

        data = {
            'type': 'accept_new_message',
            'message': TicketMessageSerializer(message).data,
        }

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)("active_support", {"type": "chat.message",
                                                           "message": json.dumps(data)})
        async_to_sync(channel_layer.group_send)(f"client_{message.tg_user.id}", {"type": "chat.message",
                                                           "message": json.dumps(data)})

        ticket.save()

    def read_message_by_support(self, data):
        message_id = data['message_id']
        cur_message = TicketMessage.objects.get(id=message_id)

        cur_message.sending_state = 'read'
        cur_message.read_by_received = True
        cur_message.save()

        responce_data = {
            'event': "response_action",
            'action': "send_message",
            'message': TicketMessageSerializer(cur_message).data,
        }
        self.send(text_data=json.dumps(responce_data))

        data = {
            'type': 'accept_read_message',
            'ok': True,
            'message': TicketMessageSerializer(cur_message).data,
        }
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)("active_support", {"type": "chat.message",
                                                          "message": json.dumps(data)})
        async_to_sync(channel_layer.group_send)(f"client_{cur_message.tg_user.id}", {"type": "chat.message",
                                                           "message": json.dumps(data)})

    @transaction.atomic()
    def close_ticket(self, data):
        chat_id = data['chat_id']
        cur_ticket = Ticket.objects.select_for_update().get(uuid=chat_id)

        if cur_ticket.status == 'closed':
            data = {
                'type': 'accept_close_ticket',
                'info': 'Тикет уже закрыт.',
                'ok': False,
                'ticket': TicketSerializer(cur_ticket).data,
            }
            self.send(json.dumps(data))
        else:

            cur_ticket.status = 'closed'
            cur_ticket.save()

            data = {
                'type': 'accept_close_ticket',
                'ok': True,
                'ticket': TicketSerializer(cur_ticket).data,
            }
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)("active_support", {"type": "chat.message",
                                                               "message": json.dumps(data)})


    def receive(self, text_data):

        data = json.loads(text_data)

        if data['event'] == 'outgoing':

            if data['action'] == 'open_chat':
                self.open_chat(data)

            elif data['action'] == 'get_messages':
                self.get_messages(data)

            elif data['action'] == 'send_message':
                self.new_message_to_client(data)

            elif data['action'] == 'read_message':
                self.read_message_by_support(data)

            elif data['action'] == 'close_ticket':
                self.close_ticket(data)
        else:
            data = {
                'message': 'Incorrect EventType',
                'ok': False,
            }

        self.send(json.dumps(data))

        # text_data_json = json.loads(text_data)
        # message = text_data_json["message"]



    def chat_message(self, event):
        event['message']['event'] = 'incoming'
        self.send(text_data=event["message"])


    def disconnect_by_heartbeat(self, event):
        self.send(text_data=event["message"])
        self.close()