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


class ClientConsumer(WebsocketConsumer):


    def connect(self):
        # print(self.channel_name)
        print(self.scope['user'])


        cur_ticket = Ticket.objects.filter(
            tg_user=self.scope["user"],
            status='created',
        )

        if not cur_ticket.exists():
            cur_ticket = Ticket(
                tg_user=self.scope["user"],
                status='created',
            )
            cur_ticket.save()
        else:
            cur_ticket = cur_ticket.first()

        last_messages = TicketMessage.objects.filter(ticket=cur_ticket).order_by('-date_created')

        # async_to_sync(self.channel_layer.group_add)(f'user_{self.scope["user"]}', self.channel_name)
        data = {}
        data['type'] = 'ticket'
        data['ticket'] = TicketSerializer(cur_ticket).data
        data['ok'] = True
        data['chat_id'] = str(cur_ticket.uuid)
        data['total_messages'] = last_messages.count()
        data['messages'] = TicketMessageSerializer(last_messages[:20], many=True).data

        print(data)
        self.accept()
        self.send(json.dumps(data))


    def disconnect(self, close_code):
        pass

    def get_messages(self, data):
        chat_id = data['chat_id']
        last_message = data['last_message_id']
        ticket = Ticket.objects.get(uuid=chat_id)
        last_messages = TicketMessage.objects.filter(ticket=ticket).order_by('-date_created')
        last_message = last_messages.get(id=last_message)

        message_to_output = last_messages.filter(date_created__lt=last_message.date_created).order_by('-date_created')

        output_data = {}
        output_data['action'] = 'get_messages'
        output_data['ok'] = True
        output_data['total_messages'] = last_messages.count()
        output_data['messages'] = TicketMessageSerializer(message_to_output[:20], many=True).data
        self.send(text_data=json.dumps(output_data))

    @transaction.atomic()
    def new_message_to_support(self, data):
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
        message.save()
        if ticket.status == 'closed':
            message.sending_state = 'failed'
            message.save()
            data = {
                'try': 'accept_new_message',
                'ok': False,
                'info': 'Тикет уже был закрыт.',
                'message': TicketMessageSerializer(message).data,
            }
        else:

            send_message_to_client.delay(message_id=message.id)

            data = {
                'try': 'accept_new_message',
                'ok': True,
                'message': TicketMessageSerializer(message).data,
            }

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)("active", {"type": "chat.message",
                                                           "message": json.dumps(data)})
        ticket.save()
    #
    # def read_message_by_support(self, data):
    #     message_id = data['message_id']
    #     cur_message = TicketMessage.objects.get(id=message_id)
    #
    #     cur_message.sending_state = 'read'
    #     cur_message.read_by_received = True
    #     cur_message.save()
    #
    #     data = {
    #         'type': 'accept_read_message',
    #         'ok': True,
    #         'message': TicketMessageSerializer(cur_message).data,
    #     }
    #     channel_layer = get_channel_layer()
    #     async_to_sync(channel_layer.group_send)("active", {"type": "chat.message",
    #                                                       "message": json.dumps(data)})
    #
    # @transaction.atomic()
    # def close_ticket(self, data):
    #     chat_id = data['chat_id']
    #     cur_ticket = Ticket.objects.select_for_update().get(uuid=chat_id)
    #
    #     if cur_ticket.status == 'closed':
    #         data = {
    #             'type': 'accept_close_ticket',
    #             'info': 'Тикет уже закрыт.',
    #             'ok': False,
    #             'ticket': TicketSerializer(cur_ticket).data,
    #         }
    #         self.send(json.dumps(data))
    #     else:
    #
    #         cur_ticket.status = 'closed'
    #         cur_ticket.save()
    #
    #         data = {
    #             'type': 'accept_close_ticket',
    #             'ok': True,
    #             'ticket': TicketSerializer(cur_ticket).data,
    #         }
    #         channel_layer = get_channel_layer()
    #         async_to_sync(channel_layer.group_send)("active", {"type": "chat.message",
    #                                                            "message": json.dumps(data)})
    #
    #
    def receive(self, text_data):

        data = json.loads(text_data)

        if data['action'] == 'get_messages':
            self.get_messages(data)

        elif data['action'] == 'send_message':
            self.new_message_to_client(data)

        elif data['action'] == 'read_message':
            self.read_message_by_support(data)

        elif data['action'] == 'close_ticket':
            self.close_ticket(data)

        # text_data_json = json.loads(text_data)
        # message = text_data_json["message"]



    def chat_message(self, event):
        self.send(text_data=event["message"])