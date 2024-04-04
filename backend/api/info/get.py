import json
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from backend.models import Ticket, User
from backend.serializers import ClientSerializer
from backend.models import TelegramBot, Platform


@transaction.atomic()
@api_view(['POST'])
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

    supporters_array = []
    supporters = User.objects.filter(platform=support_user.platform)

    for supp in supporters:
        supporters_array.append({
            "user_id": supp.id,
            "username": supp.username,
            "otp_url": supp.otp_key,
            "otp_key": f'''otpauth://totp/Gramdesk: {supp.platfrom.name}?secret={supp.otp_key}''',
            "isEditing": False,
        })

    data = {
        "ok": True,
        "email": support_user.my_email,
        "support_name": support_user.support_name,
        "username": support_user.username,
        "platform_name": platform.name if platform else '',
        "platform_description": platform.description if platform else '',
        "bot_token": bot.bot_apikey if bot else '',
        "webhook_connected": bot.webhook_connected if bot else False,
        "telegram_error": bot.message_error if bot else "",
        "code": f'''<script src="https://pashtonp.space/api/clientScript.js/{str(platform.uuid)}/"></script>''',
        "vk_callback_url": f"https://pashtonp.space/vk/{str(platform.uuid)}/" if platform.vk_access_key else "",
        "vk_access_key": platform.vk_access_key,
        "vk_confirmation_code": platform.vk_access_key,
        "supporters": supporters_array,
    }

    return Response(status=status.HTTP_200_OK, data=data)

