import datetime
import json
from json import JSONDecodeError
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer
from django.db import transaction


class UploadConsumer(WebsocketConsumer):

    def connect(self):
        from backend.models import Ticket, TicketMessage, User, SocketConnection
        from backend.serializers import TicketSerializer, TicketMessageSerializer
        print(self.channel_name)
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

        last_messages = TicketMessage.objects.filter(ticket=cur_ticket, deleted=False).order_by('-date_created')

        last_messages.filter(read_by_received=False, sender='support').update(read_by_received=True,
                                                                              sending_state='read')
        #
        # отправка саппорту по каналу инфы, что последние сообщения прочитаны
        #

        async_to_sync(self.channel_layer.group_add)(f'client_{self.scope["user"].id}', self.channel_name)
        async_to_sync(self.channel_layer.group_add)(f'active_connections', self.channel_name)


        data = {}
        data['type'] = 'ticket'
        data['ticket'] = TicketSerializer(cur_ticket, context={"from_user_type": "client"}).data
        data['ok'] = True
        data['chat_id'] = str(cur_ticket.uuid)
        data['total_messages'] = last_messages.count()
        data['messages'] = TicketMessageSerializer(last_messages[:20], many=True, context={"from_user_type": "client"}).data

        self.accept()

        new_socket_connection = SocketConnection(
            user=self.scope['user'],
            jwt=self.scope['jwt'],
            channel_name=self.channel_name,
            date_created=datetime.datetime.now().timestamp()
        )
        new_socket_connection.save()
        self.connection_id = new_socket_connection.id

        self.send(json.dumps(data))

    def disconnect(self, close_code):
        from backend.models import Ticket, TicketMessage, User, SocketConnection
        from backend.serializers import TicketSerializer, TicketMessageSerializer
        print('disconnect')
        current_connection = SocketConnection.objects.get(id=self.connection_id)
        current_connection.active = False
        current_connection.date_closed = datetime.datetime.now().timestamp()
        current_connection.save()
        async_to_sync(self.channel_layer.group_discard)(f'client_{self.scope["user"].id}', self.channel_name)
        async_to_sync(self.channel_layer.group_discard)('active_connections', self.channel_name)


    def upload_attachment(self, data):
        from backend.models import Ticket, TicketMessage, User, Attachment
        from backend.serializers import TicketSerializer, TicketMessageSerializer
        upload_data = data['upload']
        # current_attachment = Attachment.objects.select_for_update().get(id=upload_data['id'], uploaded=False)

        received_bytes = upload_data['content']

        with open(f'123.pdf', 'wb') as file:
            file.write(received_bytes)



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
