import datetime
import json
from asgiref.sync import async_to_sync, sync_to_async
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer
from django.db import transaction

from backend.models import SocketConnection


class LiveScoreConsumer(WebsocketConsumer):


    def connect(self):
        from backend.models import Ticket, TicketMessage, User
        from backend.serializers import TicketSerializer, TicketMessageSerializer
        async_to_sync(self.channel_layer.group_add)("active_support", self.channel_name)
        async_to_sync(self.channel_layer.group_add)(f'active_connections', self.channel_name)
        print(self.channel_name)

        tickets = Ticket.objects.all()

        new_tickets = tickets.filter(status='created')[:20]
        in_progress_tickets = tickets.filter(status='in_progress')[:20]
        # closed_tickets = tickets.filter(status='closed')[:20]

        new_socket_connection = SocketConnection(
            user=self.scope['user'],
            jwt=self.scope['jwt'],
            channel_name=self.channel_name,
            date_created=datetime.datetime.now().timestamp()
        )
        new_socket_connection.save()
        self.connection_id = new_socket_connection.id

        data = {}
        data['type'] = 'tickets'
        data['new_tickets'] = TicketSerializer(new_tickets, many=True, context={"from_user_type": "support"}).data
        data['in_progress_tickets'] = TicketSerializer(in_progress_tickets, many=True, context={"from_user_type": "support"}).data
        data['ok'] = True

        self.accept()
        self.send(json.dumps(data))


    def disconnect(self, close_code):
        pass

    def open_chat(self, data):
        from backend.models import Ticket, TicketMessage, User
        from backend.serializers import TicketSerializer, TicketMessageSerializer
        chat_id = data['chat_id']

        ticket = Ticket.objects.get(uuid=chat_id)
        client = ticket.tg_user
        last_messages = TicketMessage.objects.filter(ticket=ticket, deleted=False).order_by('-date_created')

        unread_message = last_messages.filter(read_by_received=False)
        unread_message.update(read_by_received=True)

        output_data = {}
        output_data['event'] = 'response_action'
        output_data['action'] = 'open_chat'
        output_data['ok'] = True
        output_data['chat_id'] = chat_id
        output_data['total_messages'] = last_messages.count()
        # output_data['client'] = ClientSerializer(client).data
        output_data['messages'] = TicketMessageSerializer(last_messages[:20], many=True, context={"from_user_type": "support"}).data
        self.send(text_data=json.dumps(output_data))

    def get_messages(self, data):
        from backend.models import Ticket, TicketMessage, User
        from backend.serializers import TicketSerializer, TicketMessageSerializer
        chat_id = data['chat_id']
        last_message = data.get('last_message_id', None)

        ticket = Ticket.objects.get(uuid=chat_id)
        last_messages = TicketMessage.objects.filter(ticket=ticket, deleted=False).order_by('-date_created')
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
        output_data['messages'] = TicketMessageSerializer(message_to_output[:20], many=True, context={"from_user_type": "support"}).data
        self.send(text_data=json.dumps(output_data))

    @transaction.atomic()
    def new_message_to_client(self, data):
        from backend.models import Ticket, TicketMessage, User, Attachment
        from backend.serializers import TicketSerializer, TicketMessageSerializer
        new_message = data['message']
        ticket = Ticket.objects.select_for_update().get(uuid=new_message['chat_id'])

        message = TicketMessage(
            tg_user=ticket.tg_user,
            employee=User.objects.all().first(),
            sender='support',
            content_type='text',
            sending_state='sent',
            message_text=new_message['content'],
            ticket=ticket,
        )
        print(new_message)

        if 'message_to_reply' in new_message:
            if new_message['message_to_reply']:
                message.message_to_reply = TicketMessage.objects.get(id=data['message_to_reply']['id'], ticket=message.ticket)


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
                        buf_size=10000,
                    ).save()
            else:
                message.save()
        else:
            message.save()

        responce_data = {
            'event': "response_action",
            'action': "send_message",
            'message': TicketMessageSerializer(message, context={"from_user_type": "support"}).data,
        }
        self.send(text_data=json.dumps(responce_data))

        if message.sending_state == 'sent':
            output_data_clients = {
                'event': "incoming",
                'type': 'new_message',
                'message': TicketMessageSerializer(message, context={"from_user_type": "client"}).data,
            }

            output_data_supports = {
                'event': "incoming",
                'type': 'new_message',
                'message': TicketMessageSerializer(message, context={"from_user_type": "support"}).data,
            }

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)("active_support", {"type": "chat.message",
                                                               "message": json.dumps(output_data_supports)})
            async_to_sync(channel_layer.group_send)(f"client_{message.tg_user.id}", {"type": "chat.message",
                                                               "message": json.dumps(output_data_clients)})

        ticket.save()

    def update_message_by_support(self, data):
        from backend.models import Ticket, TicketMessage, User
        from backend.serializers import TicketSerializer, TicketMessageSerializer
        message = data['message']
        cur_message = TicketMessage.objects.get(id=message['id'])

        if message['sending_state'] == 'read' and cur_message.sending_state == 'sent':
            cur_message.sending_state = 'read'
            cur_message.read_by_received = True

        cur_message.save()

        responce_data = {
            'event': "response_action",
            'action': "update_message",
            'message': TicketMessageSerializer(cur_message, context={"from_user_type": "support"}).data,
        }
        self.send(text_data=json.dumps(responce_data))

        data_supports = {
            'event': 'incoming',
            'type': 'update_message',
            'ok': True,
            'message': TicketMessageSerializer(cur_message, context={"from_user_type": "support"}).data,
        }
        data_clients = {
            'event': 'incoming',
            'type': 'update_message',
            'ok': True,
            'message': TicketMessageSerializer(cur_message, context={"from_user_type": "client"}).data,
        }
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)("active_support", {"type": "chat.message",
                                                          "message": json.dumps(data_supports)})
        async_to_sync(channel_layer.group_send)(f"client_{cur_message.tg_user.id}", {"type": "chat.message",
                                                           "message": json.dumps(data_clients)})


    def delete_message_by_support(self, data):
        from backend.models import Ticket, TicketMessage, User
        from backend.serializers import TicketSerializer, TicketMessageSerializer
        message = data['message']
        cur_message = TicketMessage.objects.select_for_update().get(id=message['id'])

        cur_message.deleted = True

        cur_message.save()

        responce_data = {
            'event': "response_action",
            'action': "delete_message",
            'message': TicketMessageSerializer(cur_message, context={"from_user_type": "support"}).data,
        }
        self.send(text_data=json.dumps(responce_data))

        data_supports = {
            'event': 'incoming',
            'type': 'delete_message',
            'ok': True,
            'message': TicketMessageSerializer(cur_message, context={"from_user_type": "support"}).data,
        }
        data_clients = {
            'event': 'incoming',
            'type': 'delete_message',
            'ok': True,
            'message': TicketMessageSerializer(cur_message, context={"from_user_type": "client"}).data,
        }
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)("active_support", {"type": "chat.message",
                                                          "message": json.dumps(data_supports)})
        async_to_sync(channel_layer.group_send)(f"client_{cur_message.tg_user.id}", {"type": "chat.message",
                                                           "message": json.dumps(data_clients)})


    @transaction.atomic()
    def close_ticket(self, data):
        from backend.models import Ticket, TicketMessage, User
        from backend.serializers import TicketSerializer, TicketMessageSerializer
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
                'event': "incoming",
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

            elif data['action'] == 'update_message':
                self.update_message_by_support(data)

            elif data['action'] == 'delete_message':
                self.update_message_by_support(data)

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
        self.send(text_data=event["message"])


    def disconnect_by_heartbeat(self, event):
        self.send(text_data=event["message"])
        self.close()