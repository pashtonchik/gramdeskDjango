import json
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from backend.models import Ticket, User, Platform, TelegramBot
from backend.serializers import ClientSerializer, PlatformSerializer
import pyotp
from tickets.background.telegram_bots.delete_webhook import delete_webhook_telegram
from tickets.background.telegram_bots.activate_webhook import activate_webhook_telegram


@transaction.atomic()
@api_view(['POST'])
def edit_telegram_bot(request):
    data = json.loads(request.body.decode("utf-8"))

    bot_token = data.get('bot_token')
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

    if not bot_token:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Field BotToken, BotToken is required."})

    if not TelegramBot.objects.filter(platform=support_user.platform).exists():
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False,
                              "message": "К данной платформе не привязан никакой бот, обновите страницу."})

    current_bot = TelegramBot.objects.filter(platform=support_user.platform).first()
    try:
        if current_bot.bot_apikey == bot_token:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False,
                                  "message": "Вы ввели тот же самый токен, для замены бота введите другой токен."})

    except:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False,
                              "message": "Произошла непредвиденная ошибка."})

    try:

        token = current_bot.bot_apikey
        current_bot.delete()

        transaction.on_commit(lambda: delete_webhook_telegram.delay(token))

        new_bot = TelegramBot(
            platform=support_user.platform,
            bot_apikey=bot_token
        )

        new_bot.save()
        transaction.on_commit(lambda: activate_webhook_telegram.delay(new_bot.id))

        return Response(status=status.HTTP_200_OK,
                        data={"ok": False, "message": "Бот успешно изменен, ожидайте изменения статуса для полноценной работы через Telegram."})

    except:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Произошла ошибка, попробуйте изменить данные."})