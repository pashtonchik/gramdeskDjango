import datetime
import json
from json import JSONDecodeError
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer
from django.db import transaction


class ClientConsumer(WebsocketConsumer):

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


    def get_messages(self, data):
        from backend.models import Ticket, TicketMessage, User, SocketConnection
        from backend.serializers import TicketSerializer, TicketMessageSerializer
        chat_id = data['chat_id']
        last_message = data.get('last_message_id', None)
        ticket = Ticket.objects.get(uuid=chat_id)
        last_messages = TicketMessage.objects.filter(ticket=ticket, deleted=False).order_by('-date_created')
        if last_message:
            last_message = last_messages.get(id=last_message)

            message_to_output = last_messages.filter(date_created__lt=last_message.date_created).order_by(
                '-date_created')

        else:
            message_to_output = last_messages.order_by('-date_created')

        output_data = {}
        output_data['event'] = 'response_action'
        output_data['action'] = 'get_messages'
        output_data['ok'] = True
        output_data['total_messages'] = last_messages.count()
        output_data['messages'] = TicketMessageSerializer(message_to_output[:20], many=True, context={"from_user_type": "client"}).data
        self.send(text_data=json.dumps(output_data))

    @transaction.atomic()
    def new_message_to_support(self, data):
        from backend.models import Ticket, TicketMessage, User, SocketConnection
        from backend.serializers import TicketSerializer, TicketMessageSerializer
        new_message = data['message']
        ticket = Ticket.objects.select_for_update().get(uuid=new_message['chat_id'], tg_user=self.scope['user'])

        if ticket.status == 'inactive':
            ticket.status = 'created'

        message = TicketMessage(
            tg_user=ticket.tg_user,
            employee=User.objects.all().first(),
            sender='client',
            content_type='text',
            sending_state='sent',
            message_text=new_message['content'],
            ticket=ticket,
        )

        if 'message_to_reply' in data:
            if data['message_to_reply']:
                message.message_to_reply = TicketMessage.objects.get(id=data['message_to_reply']['id'], ticket=message.ticket)

        message.save()

        responce_data = {
            'event': "response_action",
            'action': "read_message",
            'message': TicketMessageSerializer(message, context={"from_user_type": "client"}).data,
        }
        self.send(text_data=json.dumps(responce_data))

        data_clients = {
            'event': "incoming",
            'type': 'new_message',
            'message': TicketMessageSerializer(message, context={"from_user_type": "client"}).data,
        }

        data_supports = {
            'event': "incoming",
            'type': 'new_message',
            'message': TicketMessageSerializer(message, context={"from_user_type": "support"}).data,
        }

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(f"client_{message.tg_user.id}", {"type": "chat.message",
                                                           "message": json.dumps(data_clients)})

        async_to_sync(channel_layer.group_send)(f"active_support", {"type": "chat.message",
                                                           "message": json.dumps(data_supports)})
        ticket.save()

    def update_message_by_client(self, data):
        from backend.models import Ticket, TicketMessage, User, SocketConnection
        from backend.serializers import TicketSerializer, TicketMessageSerializer
        message = data['message']
        cur_message = TicketMessage.objects.get(id=message['id'])

        if message['sending_state'] == 'read' and cur_message.sending_state == 'sent':
            cur_message.sending_state = 'read'
            cur_message.read_by_received = True
            cur_message.save()


        response_data = {
            'event': "response_action",
            'action': "update_message",
            'message': TicketMessageSerializer(cur_message, context={"from_user_type": "client"}).data,
        }
        self.send(text_data=json.dumps(response_data))
        data_clients = {
            'event': 'incoming',
            'type': 'update_message',
            'message': TicketMessageSerializer(cur_message, context={"from_user_type": "client"}).data,
        }
        data_supports = {
            'event': 'incoming',
            'type': 'update_message',
            'message': TicketMessageSerializer(cur_message, context={"from_user_type": "support"}).data,
        }

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)("active_support", {"type": "chat.message",
                                                          "message": json.dumps(data_supports)})
        async_to_sync(channel_layer.group_send)(f"client_{cur_message.tg_user.id}", {"type": "chat.message",
                                                           "message": json.dumps(data_clients)})

    def delete_message_by_client(self, data):
        from backend.models import Ticket, TicketMessage, User, SocketConnection
        from backend.serializers import TicketSerializer, TicketMessageSerializer
        message_id = data['message_id']
        cur_message = TicketMessage.objects.get(id=message_id)

        if data['message']['sending_state'] == 'read' and cur_message.sending_state == 'sent':
            cur_message.sending_state = 'read'
            cur_message.read_by_received = True
            cur_message.save()


        response_data = {
            'event': "response_action",
            'action': "update_message",
            'message': TicketMessageSerializer(cur_message, context={"from_user_type": "client"}).data,
        }
        self.send(text_data=json.dumps(response_data))
        data_clients = {
            'event': 'incoming',
            'type': 'update_message',
            'message': TicketMessageSerializer(cur_message, context={"from_user_type": "client"}).data,
        }
        data_supports = {
            'event': 'incoming',
            'type': 'update_message',
            'message': TicketMessageSerializer(cur_message, context={"from_user_type": "support"}).data,
        }

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)("active_support", {"type": "chat.message",
                                                          "message": json.dumps(data_supports)})
        async_to_sync(channel_layer.group_send)(f"client_{cur_message.tg_user.id}", {"type": "chat.message",
                                                           "message": json.dumps(data_clients)})

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
                    if data['action'] == 'get_messages':
                        self.get_messages(data)

                    elif data['action'] == 'send_message':
                        self.new_message_to_support(data)

                    elif data['action'] == 'update_message':
                        self.update_message_by_client(data)

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
