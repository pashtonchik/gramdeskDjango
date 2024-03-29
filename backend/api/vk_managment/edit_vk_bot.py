import json

import requests
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from backend.models import Ticket, User, Platform, TelegramBot
from backend.serializers import ClientSerializer, PlatformSerializer, TelegramBotSerializer
import pyotp
from tickets.background.vk_bots.delete_webhook import delete_webhook_vk


@transaction.atomic()
@api_view(['POST'])
def edit_vk_bot(request):
    data = json.loads(request.body.decode("utf-8"))

    access_token = data.get('access_token')
    confirmation_code = data.get('confirmation_code')
    code = data.get('code')

    try:
        support_user = User.objects.get(id=request.user.id)
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Произошла ошибка, обновите страницу."})

    if not code:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Field Code, Code is required."})

    if not confirmation_code:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Field Confirmation Code, Confirmation Code is required."})

    if not pyotp.TOTP(request.user.otp_key).verify(code, valid_window=1):
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Одноразовый пароль неверен, повторите Вашу попытку."})

    if not access_token:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Field access_token, access_token is required."})

    # if not TelegramBot.objects.filter(platform=support_user.platform).exists():
    #     return Response(status=status.HTTP_400_BAD_REQUEST,
    #                     data={"ok": False,
    #                           "message": "К данной платформе не привязан никакой бот, обновите страницу."})

    platform = Platform.objects.get(admin=support_user)


    try:
        if platform.vk_access_key == access_token:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False,
                                  "message": "Вы ввели тот же самый токен, для замены бота введите другой токен."})

    except:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False,
                              "message": "Произошла непредвиденная ошибка."})

    try:
        if platform.vk_access_key:
            token = platform.vk_access_key

            transaction.on_commit(lambda: delete_webhook_vk.delay(token))

        platform.vk_access_key = access_token
        platform.vk_confirmation_code = confirmation_code

        platform.save()

        # try:
        #     req = requests.get(f"https://api.telegram.org/bot{new_bot.bot_apikey}/setwebhook?url=https://pashtonp.space/tg_bots/{new_bot.bot_apikey}")
        #
        #     data = req.json()
        #     print(data)
        #
        #     if data['ok'] and data['result'] and req.status_code == 200:
        #         new_bot.webhook_connected = True
        #     else:
        #         new_bot.message_error = data['description']
        #         new_bot.webhook_connected = False
        # except:
        #     new_bot.message_error = "Произошла ошибка, в токене ошибка."
        #     print("Какая то ошибка")

        # new_bot.save()
        data = {
            'ok': True,
            "message": "Бот успешно изменен.",
            "vk_confirmation_code": platform.vk_confirmation_code,
            "vk_access_key": platform.vk_access_key,
        }


        return Response(status=status.HTTP_200_OK,
                        data=data)

    except:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Произошла ошибка, попробуйте изменить данные."})