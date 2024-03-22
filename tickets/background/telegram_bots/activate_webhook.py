import requests
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async
from celery import shared_task
from django.db import transaction
import json


@shared_task()
def activate_webhook_telegram(bot_id):
    from backend.models import TelegramBot
    with transaction.atomic():
        bot = TelegramBot.objects.select_for_update().get(id=bot_id)

        try:
            req = requests.get(f"https://api.telegram.org/bot{bot.bot_apikey}/setwebhook?url=https://pashtonp.space/tg_bots/{bot.bot_apikey}")

            data = req.json()
            print(data)

            if data['ok'] and data['result']:
                bot.webhook_connected = True
            else:
                bot.message_error = data['description']
        except:
            bot.message_error = "Произошла ошибка, в токене ошибка."
            print("Какая то ошибка")

        bot.save()



@shared_task()
def send_message_read_messages(ids_array):
    from backend.models import TicketMessage
    from backend.serializers import TicketMessageSerializer
    messages = TicketMessage.objects.filter(id__in=ids_array)

    for message in messages:

        data = {
            'event': 'incoming',
            'type': 'update_message',
            'ok': True,
            'message': TicketMessageSerializer(message, context={"from_user_type": message.sender}).data,
        }

        channel_layer = get_channel_layer()
        if message.sender == "support":
            async_to_sync(channel_layer.group_send)("active_support", {"type": "chat.message",
                                                                   "message": json.dumps(data)})
        else:
            async_to_sync(channel_layer.group_send)(f"client_{message.tg_user.id}", {"type": "chat.message",
                                                                                     "message": json.dumps(data)})

