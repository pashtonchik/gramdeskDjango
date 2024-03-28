import datetime
import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from backend.models import *
from backend.serializers import TicketMessageSerializer, TicketSerializer
from tickets.background.telegram_bots.activate_webhook import send_message_read_messages
from tickets.background.vk.get_file import get_file
from django.http import HttpResponse


@transaction.atomic()
@api_view(['POST'])
def vk_event(request, platform_id):
    try:
        data = json.loads(request.body.decode("utf-8"))
        print(data)

        platforms = Platform.objects.filter(uuid=platform_id)
        if platforms.exists():
            platform = platforms.first()
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": "Platform does not exist."})

        if data.get("type") == "confirmation":
            code = platform.vk_confirmation_code
            return HttpResponse(f"{code}")
        elif data.get("type") == "message_new":
            if TicketMessage.objects.filter(vk_message_id=data.get('object', {}).get('message', {}).get('id', "0")).exists():
                return Response(status=status.HTTP_200_OK,
                                data={"ok": False, "message": "This Message already exists."})
            # platform = TelegramBot.objects.get(bot_apikey=token)
            #
            #
            users = User.objects.filter(vk_id=data.get('object', {}).get('message', {}).get('from_id', "0"), type='client', source="vk")

            if users.exists():
                cur_user = users.first()
                if cur_user.is_blocked:
                    return Response(status=status.HTTP_200_OK, data={"ok": True})

            else:
                cur_user = User(
                    username=User.objects.all().count() + 1,
                    type='client',
                    source='vk',
                    vk_id=data.get('object', {}).get('message', {}).get('from_id', "Не известно"),
                    vk_username=User.objects.all().count() + 1,
                )
                cur_user.save()


            tickets = Ticket.objects.select_for_update().filter(tg_user=cur_user, status__in=['created', 'in_progress'], platform=platform)

            if not tickets.exists():
                cur_ticket = Ticket(
                    source='vk',
                    platform=platform,
                    tg_user=cur_user,
                    status='created',
                    date_last_message=datetime.datetime.now(),
                )
                cur_ticket.save()
                is_new_ticket = True
            else:
                cur_ticket = tickets.order_by('-date_created').first()
                is_new_ticket = False

            if data.get('object', {}).get('message', {}).get('attachments', []) != []:
                new_message = TicketMessage(
                    tg_user=cur_user,
                    sender='client',
                    content_type='file',
                    sending_state='uploading_attachments',
                    message_text=data.get('object', {}).get('message', {}).get('text', ""),
                    ticket=cur_ticket,
                )
                new_message.save()

                get_file.delay(new_message.id, data, is_new_ticket)

            # if data.get('message', {}).get('photo', None):
            #     new_message = TicketMessage(
            #         tg_user=cur_user,
            #         sender='client',
            #         content_type='file',
            #         sending_state='uploading_attachments',
            #         message_text=data.get('message', {}).get('caption', ''),
            #         ticket=cur_ticket,
            #     )
            #     new_message.save()
            #
            #     get_file.delay(new_message.id, data, is_new_ticket)
            #
            if data.get('object', {}).get('message', {}).get("attachments", []) == []:
                new_message = TicketMessage(
                    tg_user=cur_user,
                    sender='client',
                    content_type='text',
                    sending_state='sent',
                    message_text=data['object']['message']['text'],
                    ticket=cur_ticket,
                    vk_message_id=data.get('object', {}).get('message', {}).get("id", "0")
                )
                new_message.save()

                channel_layer = get_channel_layer()

                data = {
                    'event': "incoming",
                    'type': 'new_message',
                    'message': TicketMessageSerializer(new_message, context={"from_user_type": "support"}).data
                }

                if is_new_ticket:
                    data["new_ticket"] = TicketSerializer(cur_ticket, context={"from_user_type": "support"}).data
                cur_ticket.date_last_message = datetime.datetime.now()
                cur_ticket.save()
                async_to_sync(channel_layer.group_send)(f"support_{cur_ticket.platform.uuid}", {"type": "chat.message",
                                                              "message": json.dumps(data)})
                new_message.sending_state = 'delivered'
                new_message.save()


                unread_messages = TicketMessage.objects.select_for_update().filter(sending_state="delivered", sender="support")
                array = [*unread_messages.values_list('id', flat=True)]
                unread_messages.update(sending_state="read", read_by_received=True)

                send_message_read_messages.delay(array, "support")
            return Response(status=status.HTTP_200_OK, data=data)
    except Exception as e:
        print(e)
        return Response(status=status.HTTP_200_OK)
