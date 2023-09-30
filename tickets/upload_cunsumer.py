import base64
import datetime
import json
from json import JSONDecodeError
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer
from django.db import transaction


class UploadConsumer(WebsocketConsumer):

    def connect(self):
        # async_to_sync(self.channel_layer.group_add)("active_support", self.channel_name)
        # async_to_sync(self.channel_layer.group_add)(f'active_connections', self.channel_name)
        # print(self.channel_name)

        # closed_tickets = tickets.filter(status='closed')[:20]

        data = {}

        self.accept()
        self.send(json.dumps(data))




    def disconnect(self, close_code):
        from backend.models import Ticket, TicketMessage, User, SocketConnection
        from backend.serializers import TicketSerializer, TicketMessageSerializer
        pass
        # print('disconnect')
        # current_connection = SocketConnection.objects.get(id=self.connection_id)
        # current_connection.active = False
        # current_connection.date_closed = datetime.datetime.now().timestamp()
        # current_connection.save()
        # async_to_sync(self.channel_layer.group_discard)(f'client_{self.scope["user"].id}', self.channel_name)
        # async_to_sync(self.channel_layer.group_discard)('active_connections', self.channel_name)


    def upload_attachment(self, data):
        from backend.models import Ticket, TicketMessage, User, Attachment
        from backend.serializers import TicketSerializer, TicketMessageSerializer
        upload_data = data['upload_data']
        # current_attachment = Attachment.objects.select_for_update().get(id=upload_data['id'], uploaded=False)

        received_bytes = upload_data['content']
        print(len(base64.b64decode(received_bytes.encode('UTF-8'))))
        print('file')
        with open(f'123.pdf', 'ab+') as file:
            file.write(base64.b64decode(received_bytes.encode('UTF-8')))



    def receive(self, text_data):
        from backend.models import Ticket, TicketMessage, User, SocketConnection
        from backend.serializers import TicketSerializer, TicketMessageSerializer
        if text_data == 'heartbeat':
            current_connection = SocketConnection.objects.get(channel_name=self.channel_name)
            current_connection.approve_heartbeat = True
            current_connection.save()
        else:

            try:
                data = json.loads(text_data)
                if data['event'] == 'outgoing':
                    if data['action'] == 'upload':
                        print(1)
                        self.upload_attachment(data)

                    else:
                        data = {
                            'message': 'Incorrect Action',
                            'ok': False,
                        }

                        self.send(json.dumps(data))
                else:
                    data = {
                        'message': 'Incorrect EventType',
                        'ok': False,
                    }

                    self.send(json.dumps(data))



            except JSONDecodeError:
                data = {
                    'message': 'Incorrect Message',
                    'ok': False,
                }

                self.send(json.dumps(data))

    def chat_message(self, event):
        self.send(text_data=event["message"])

    def disconnect_by_heartbeat(self, event):
        self.send(text_data=event["message"])
        self.close()