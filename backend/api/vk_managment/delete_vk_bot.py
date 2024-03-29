import json
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from backend.models import Ticket, User, Platform, TelegramBot
from backend.serializers import ClientSerializer, PlatformSerializer
import pyotp
from tickets.background.vk_bots.delete_webhook import delete_webhook_vk


@transaction.atomic()
@api_view(['POST'])
def delete_vk_bot(request):
    data = json.loads(request.body.decode("utf-8"))

    code = data.get('code')

    try:
        support_user = User.objects.get(id=request.user.id)
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Произошла ошибка, обновите страницу."})

    if not code:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Field Code, Code is required."})

    if not pyotp.TOTP(request.user.otp_key).verify(code, valid_window=1):
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Одноразовый пароль неверен, повторите Вашу попытку."})


    if Platform.objects.get(admin=support_user).vk_access_key == "":
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False,
                              "message": "К данной платформе не привязан никакой бот, обновите страницу."})


    platform = Platform.objects.get(admin=support_user)


    try:
        if platform.vk_access_key:
            token = platform.vk_access_key

            transaction.on_commit(lambda: delete_webhook_vk.delay(token=token))

        platform.vk_access_key = ""
        platform.vk_confirmation_code = ""
        platform.vk_webhook_connected = False

        platform.save()

        return Response(status=status.HTTP_200_OK,
                        data={"ok": True, "message": "Бот успешно удален."})

    except:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Произошла ошибка, попробуйте изменить данные."})

