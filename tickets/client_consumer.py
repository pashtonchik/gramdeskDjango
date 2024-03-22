import datetime
import json
from json import JSONDecodeError
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer
from django.db import transaction
from tickets.background.telegram_bots.read_messages import send_message_read_messages

from backend.models import Attachment


class ClientConsumer(WebsocketConsumer):

    def connect(self):
        from backend.models import Ticket, SocketConnection
        from backend.serializers import TicketSerializer
        print(self.channel_name)
        print(self.scope['user'])
        cur_tickets = Ticket.objects.filter(
            tg_user=self.scope["user"],
            status='created',
        )

        if not cur_tickets.exists():
            cur_ticket = Ticket(
                tg_user=self.scope["user"],
                status='created',
                platform=self.scope["platform"],
                source="widget",

            )
            cur_ticket.save()

        cur_tickets = Ticket.objects.filter(
            tg_user=self.scope["user"],
            status='created',
        )

        # last_messages = TicketMessage.objects.filter(ticket=cur_tickets, deleted=False).order_by('-date_created')

        # last_messages.filter(read_by_received=False, sender='support').update(read_by_received=True,
        #                                                                       sending_state='read')
        #
        # отправка саппорту по каналу инфы, что последние сообщения прочитаны
        #

        async_to_sync(self.channel_layer.group_add)(f'client_{self.scope["user"].id}', self.channel_name)
        async_to_sync(self.channel_layer.group_add)(f'active_connections', self.channel_name)


        data = {}
        data['type'] = 'tickets'
        data['new_tickets'] = TicketSerializer(cur_tickets, many=True, context={"from_user_type": "client"}).data
        data['in_progress_tickets'] = []
        data['ok'] = True

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
        from backend.models import SocketConnection
        print('disconnect')
        current_connection = SocketConnection.objects.get(id=self.connection_id)
        current_connection.active = False
        current_connection.date_closed = datetime.datetime.now().timestamp()
        current_connection.save()
        async_to_sync(self.channel_layer.group_discard)(f'client_{self.scope["user"].id}', self.channel_name)
        async_to_sync(self.channel_layer.group_discard)('active_connections', self.channel_name)


    def get_messages(self, data):
        from backend.models import Ticket, TicketMessage
        from backend.serializers import TicketMessageSerializer
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

        ids_messages_to_output = message_to_output[:20].values_list('id', flat=True)

        if message_to_output.filter(id__in=ids_messages_to_output, sender="support", sending_state="delivered").exists():
            message_to_output.filter(id__in=ids_messages_to_output, sender="support", sending_state="delivered").update(
                sending_state="read")
            send_message_read_messages.delay(ids_messages_to_output)

        output_data = {}
        output_data['event'] = 'response_action'
        output_data['action'] = 'get_messages'
        output_data['ok'] = True
        output_data['total_messages'] = last_messages.count()
        output_data['messages'] = TicketMessageSerializer(message_to_output[:20], many=True, context={"from_user_type": "client"}).data
        self.send(text_data=json.dumps(output_data))

    @transaction.atomic()
    def new_message_to_support(self, data):
        from backend.models import Ticket, TicketMessage, User
        from backend.serializers import TicketMessageSerializer
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

        message.save()

        responce_data = {
            'event': "response_action",
            'action': "send_message",
            'message': TicketMessageSerializer(message, context={"from_user_type": "client"}).data,
        }
        self.send(text_data=json.dumps(responce_data))

        if message.sending_state == 'sent':
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
            message.sending_state = "delivered"
            message.save()
        ticket.save()

    def update_message_by_client(self, data):
        from backend.models import TicketMessage
        from backend.serializers import TicketMessageSerializer
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
        from backend.models import TicketMessage
        from backend.serializers import TicketMessageSerializer
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
        from backend.models import SocketConnection
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
