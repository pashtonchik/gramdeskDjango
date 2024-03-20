import requests
from celery import shared_task


@shared_task()
def activate_webhook_telegram(bot_id):
    from backend.models import TelegramBot

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

