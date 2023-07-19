# Встроенные импорты.
import json

from asgiref.sync import async_to_sync
from channels.consumer import AsyncConsumer
# Импорты сторонних библиотек.
from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer

# Импорты Django.
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import AnonymousUser

from backend.models import Ticket, TicketMessage
from backend.serializers import TicketSerializer, ClientSerializer, TicketMessageSerializer


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
        last_messages = TicketMessage.objects.filter(ticket=ticket)[:20]

        output_data = {}
        output_data['action'] = 'open_chat'
        output_data['client'] = ClientSerializer(client).data
        output_data['messages'] = TicketMessageSerializer(last_messages, many=True).data
        self.send(text_data=json.dumps({"message": '789'}))





    def receive(self, text_data):
        print(text_data)

        data = json.loads(text_data)

        if data['action'] == 'open_chat':
            self.open_chat(data)

        # text_data_json = json.loads(text_data)
        # message = text_data_json["message"]

        self.send(text_data=json.dumps({"message": '123'}))



    def chat_message(self, event):
        self.send(text_data=event["message"])