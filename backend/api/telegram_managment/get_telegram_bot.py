import json
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from backend.models import Ticket, User, TelegramBot
from backend.serializers import TelegramBotSerializer


@transaction.atomic()
@api_view(['GET'])
def get_telegram_bot(request):
    try:
        support_user = request.user
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Произошла ошибка, обновите страницу."})

    if not TelegramBot.objects.filter(platform=support_user.platform).exists():
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False,
                              "message": "К данной платформе не привязан никакой бот, обновите страницу."})

    current_bot = TelegramBot.objects.filter(platform=support_user.platform).first()

    data = TelegramBotSerializer(current_bot).data

    return Response(status=status.HTTP_200_OK, data=data)

