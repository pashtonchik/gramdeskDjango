from celery import shared_task
import requests
from django.db import transaction
from datetime import datetime


@shared_task(bind=True)
def send_media(self, message_id):
    from backend.models import TicketMessage, Attachment, TelegramBot
    try:
        with transaction.atomic():
            msg = TicketMessage.objects.select_for_update().get(id=message_id)
            bot_apikey = TelegramBot.objects.get(platform=msg.ticket.platform).bot_apikey
            for media in Attachment.objects.filter(message=msg):
                data = {
                    "chat_id": msg.tg_user.tg_id,
                    "caption": f'{msg.message_text}',
                    "parse_mode": "HTML"
                }
                print(data)
                send_code = requests.get(
                    f"https://api.telegram.org/bot{bot_apikey}/sendDocument", data=data, files={
                        'document': open(media.file, "rb")
                    })

                print(send_code.text)

                if send_code.status_code != 200:
                    print(send_code.text)
                    raise Exception

    except Exception as e:
        print(e)