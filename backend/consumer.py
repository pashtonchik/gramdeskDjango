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


class LiveScoreConsumer(WebsocketConsumer):
    def connect(self):
        async_to_sync(self.channel_layer.group_add)("chat1", self.channel_name)
        print(self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        print(text_data)
        # text_data_json = json.loads(text_data)
        # message = text_data_json["message"]

        self.send(text_data=json.dumps({"message": '123'}))

    def chat_message(self, event):
        self.send(text_data=event["message"])