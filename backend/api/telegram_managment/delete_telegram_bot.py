import json
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from backend.models import Ticket, User, Platform, TelegramBot
from backend.serializers import ClientSerializer, PlatformSerializer
import pyotp
from tickets.background.telegram_bots.delete_webhook import delete_webhook_telegram


@transaction.atomic()
@api_view(['POST'])
def delete_telegram_bot(request, token):
    data = json.loads(request.body.decode("utf-8"))

    code = data.get('code')

    try:
        support_user = request.user
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Произошла ошибка, обновите страницу."})

    if not code:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Field Code, Code is required."})

    if not pyotp.TOTP(request.user.otp_key).verify(code, valid_window=1):
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Одноразовый пароль неверен, повторите Вашу попытку."})


    if not TelegramBot.objects.filter(platform=support_user.platform).exists():
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False,
                              "message": "К данной платформе не привязан никакой бот, обновите страницу."})

    current_bot = TelegramBot.objects.filter(platform=support_user.platform).first()


    try:

        token = current_bot.bot_apikey
        current_bot.delete()

        transaction.on_commit(lambda: delete_webhook_telegram.delay(token))

    except:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Произошла ошибка, попробуйте изменить данные."})


    else:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Такой платформы не найдено."})