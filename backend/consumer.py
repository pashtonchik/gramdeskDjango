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

from backend.models import Ticket
from backend.serializers import TicketSerializer


class LiveScoreConsumer(WebsocketConsumer):
    def connect(self):
        async_to_sync(self.channel_layer.group_add)("chat1", self.channel_name)
        print(self.channel_name)

        tickets = Ticket.objects.all()

        new_tickets = tickets.filter(status='created')[:20]
        in_progress_tickets = tickets.filter(status='in_progress')[:20]
        # closed_tickets = tickets.filter(status='closed')[:20]


        data = TicketSerializer(new_tickets, many=True).data + TicketSerializer(in_progress_tickets, many=True).data


        self.accept()
        self.send(json.dumps(data))

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        print(text_data)
        # text_data_json = json.loads(text_data)
        # message = text_data_json["message"]

        self.send(text_data=json.dumps({"message": '123'}))

    def chat_message(self, event):
        self.send(text_data=event["message"])