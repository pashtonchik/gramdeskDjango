import requests
from celery import shared_task


@shared_task(bind=True)
def delete_webhook_vk(self, token):

    try:

        auth = {
            "Authorization": "Bearer " + token
        }

        req = requests.get(f"https://api.vk.com/method/account.removeWebHook?v=5.199", headers=auth)

        data = req.json()
        print(data)

    except:
        print("Какая то ошибка")