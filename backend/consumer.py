# Встроенные импорты.
import json

from asgiref.sync import async_to_sync, sync_to_async
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
# Импорты сторонних библиотек.
from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer

# Импорты Django.
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import AnonymousUser

from backend.models import Ticket, TicketMessage, SupportUser
from backend.serializers import TicketSerializer, ClientSerializer, TicketMessageSerializer
from tickets.celery_tasks.send_message_to_client import send_message_to_client


class LiveScoreConsumer(WebsocketConsumer):


    def connect(self):
        async_to_sync(self.channel_layer.group_add)("chat1", self.channel_name)
        print(self.channel_name)

        tickets = Ticket.objects.all()

        new_tickets = tickets.filter(status='created')[:20]
        in_progress_tickets = tickets.filter(status='in_progress')[:20]
        # closed_tickets = tickets.filter(status='closed')[:20]

        data = {}

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

        output_data = {}
        output_data['action'] = 'open_chat'
        output_data['total_messages'] = last_messages.count()
        output_data['client'] = ClientSerializer(client).data
        output_data['messages'] = TicketMessageSerializer(last_messages[:20], many=True).data
        self.send(text_data=json.dumps(output_data))


    def get_messages(self, data):
        chat_id = data['chat_id']
        last_message = data['last_message_id']
        ticket = Ticket.objects.get(uuid=chat_id)
        last_messages = TicketMessage.objects.filter(ticket=ticket).order_by('-date_created')
        last_message = last_messages.get(id=last_message)

        message_to_output = last_messages.filter(date_created__lt=last_message.date_created).order_by('-date_created')

        output_data = {}
        output_data['action'] = 'get_messages'
        output_data['total_messages'] = last_messages.count()
        output_data['messages'] = TicketMessageSerializer(message_to_output[:20], many=True).data
        self.send(text_data=json.dumps(output_data))


    def new_message_to_client(self, data):
        new_message = data['message']
        ticket = Ticket.objects.get(uuid=new_message['chat_id'])

        message = TicketMessage(
            tg_user=ticket.tg_user,
            employee=SupportUser.objects.all().first(),
            sender='employee',
            content_type='text',
            sending_state='sent',
            message_text=new_message['content'],
            ticket=ticket,
        )

        message.save()

        send_message_to_client.delay(message_id=message.id)

        data = {
            'ok': True,
            'message': TicketMessageSerializer(message).data,
        }



        self.send(text_data=json.dumps(data))

    def receive(self, text_data):

        data = json.loads(text_data)

        if data['action'] == 'open_chat':
            self.open_chat(data)

        elif data['action'] == 'get_messages':
            self.get_messages(data)

        elif data['action'] == 'send_message':
            self.new_message_to_client(data)

        # text_data_json = json.loads(text_data)
        # message = text_data_json["message"]



    def chat_message(self, event):
        self.send(text_data=event["message"])