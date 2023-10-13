import base64
import datetime
import json
import logging
from json import JSONDecodeError
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer
from django.core.files.base import ContentFile

from backend.models import SocketConnection
from backend.serializers import AttachmentSerializer

logger = logging.getLogger('main')
class DownloadConsumer(WebsocketConsumer):

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


    def send_attachment(self, data):
        from backend.models import TicketMessage, Attachment
        from backend.serializers import TicketMessageSerializer
        logger.info(data['attachment'])
        attachment_id = data['attachment']['id']
        sent_bytes = data['attachment'].get('received_bytes', 0)

        current_attachment = Attachment.objects.select_for_update().get(id=attachment_id)

        if current_attachment.total_bytes <= sent_bytes or sent_bytes < 0:
            logger.info("Пришла хуйня дисконект")
            self.disconnect()
            return "disconnect"

        if current_attachment.received_bytes < current_attachment.total_bytes:
            logger.info("Файл еще даже не дозагрузился биля, куда ты лезешь")
            self.disconnect()
            return "disconnect"

        with current_attachment.file.open(mode='rb') as file:
            print(1)
            file.seek(sent_bytes, 0)
            bytes = file.read(current_attachment.buf_size)
            file = base64.b64encode(bytes).decode('UTF-8')


        responce_data = {
            'event': "response_action",
            'action': "get_attachment",
            'content': file,
            'total_size': current_attachment.total_bytes,
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
                    if data['action'] == 'get_attachment':
                        self.send_attachment(data)
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
