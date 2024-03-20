import requests
from celery import shared_task


@shared_task()
def delete_webhook_telegram(token):

    try:
        req = requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook")

        data = req.json()
        print(data)

    except:
        print("Какая то ошибка")
