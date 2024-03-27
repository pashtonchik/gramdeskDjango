import json
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from backend.models import Ticket, User
from backend.serializers import ClientSerializer
from backend.models import TelegramBot, Platform


@transaction.atomic()
@api_view(['GET'])
def get_info(request):

    try:
        support_user = User.objects.get(id=request.user.id)
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": "Произошла ошибка, обновите страницу."})


    if TelegramBot.objects.filter(platform__admin=request.user):
        bot = TelegramBot.objects.get(platform__admin=request.user)
    else:
        bot = None

    if Platform.objects.filter(admin=request.user):
        platform = Platform.objects.get(admin=request.user)
    else:
        platform = None

    data = {
        "ok": True,
        "username": support_user.username,
        "platform_name": platform.name if platform else '',
        "platform_description": platform.description if platform else '',
        "bot_token": bot.bot_apikey if bot else '',
        "webhook_connected": bot.webhook_connected if bot else False,
    }

    return Response(status=status.HTTP_200_OK, data=data)

