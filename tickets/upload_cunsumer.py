import base64
import datetime
import json
from json import JSONDecodeError
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer
from django.core.files.base import ContentFile

from backend.models import SocketConnection
from backend.serializers import AttachmentSerializer


class UploadConsumer(WebsocketConsumer):

    def connect(self):
        async_to_sync(self.channel_layer.group_add)(f'active_connections', self.channel_name)
        print(self.channel_name)

        # closed_tickets = tickets.filter(status='closed')[:20]
        new_socket_connection = SocketConnection(
            user=self.scope['user'],
            jwt=self.scope['jwt'],
            channel_name=self.channel_name,
            date_created=datetime.datetime.now().timestamp()
        )
        new_socket_connection.save()
        self.connection_id = new_socket_connection.id

        data = {
            'ok': True
        }

        self.accept()
        self.send(json.dumps(data))




    def disconnect(self, close_code):
        from backend.models import SocketConnection
        print('disconnect')
        current_connection = SocketConnection.objects.get(id=self.connection_id)
        current_connection.active = False
        current_connection.date_closed = datetime.datetime.now().timestamp()
        current_connection.save()
        async_to_sync(self.channel_layer.group_discard)('active_connections', self.channel_name)


    def upload_attachment(self, data):
        from backend.models import TicketMessage, Attachment
        from backend.serializers import TicketMessageSerializer
        upload_data = data['upload_data']

        current_attachment = Attachment.objects.select_for_update().get(id=upload_data['id'], uploaded=False)
        # current_attachment = Attachment.objects.select_for_update().get(id=upload_data['id'], uploaded=False)
        received_bytes = upload_data['content']
        content = base64.b64decode(received_bytes.encode('UTF-8'))
        current_attachment.received_bytes += len(base64.b64decode(received_bytes.encode('UTF-8')))
        current_attachment.content += received_bytes
        print('file')
        # with open(f'123.pdf', 'ab+') as file:
        #     file.write(base64.b64decode(received_bytes.encode('UTF-8')))

        if current_attachment.total_bytes == current_attachment.received_bytes:
            current_attachment.file.save(name=current_attachment.name + '.' + current_attachment.ext,
                                         content=ContentFile(base64.b64decode(current_attachment.content)),
                                         save=True
                                         )
            current_attachment.uploaded = True

            current_attachment.save()

            if not Attachment.objects.filter(message=current_attachment.message, uploaded=False).exists():
                current_message = TicketMessage.objects.select_for_update().get(id=current_attachment.id)
                current_message.sending_state = 'sent'

                output_data_clients = {
                    'event': "incoming",
                    'type': 'new_message',
                    'message': TicketMessageSerializer(current_message, context={"from_user_type": "client"}).data,
                }

                output_data_supports = {
                    'event': "incoming",
                    'type': 'new_message',
                    'message': TicketMessageSerializer(current_message, context={"from_user_type": "support"}).data,
                }

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)("active_support", {"type": "chat.message",
                                                                           "message": json.dumps(output_data_supports)})
                async_to_sync(channel_layer.group_send)(f"client_{current_message.tg_user.id}", {"type": "chat.message",
                                                                                         "message": json.dumps(
                                                                                             output_data_clients)})
        else:
            current_attachment.save()

        responce_data = {
            'event': "response_action",
            'action': "upload",
            'message': AttachmentSerializer(current_attachment).data,
        }
        self.send(text_data=json.dumps(responce_data))


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



            except (JSONDecodeError, KeyError):
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
