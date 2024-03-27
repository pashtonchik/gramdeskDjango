import json
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from backend.models import Ticket, User, Platform
from backend.serializers import ClientSerializer, PlatformSerializer
import pyotp


@transaction.atomic()
@api_view(['POST'])
def update_platform_info(request):
    data = json.loads(request.body.decode("utf-8"))

    user_id = data.get('id')
    new_name = data.get('new_name')
    new_description = data.get('new_description')
    code = data.get('code')

    try:
        support_user = request.user
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Произошла ошибка, обновите страницу."})

    if not code:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": "Field Code, Code is required."})

    if not user_id:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": "Field id, id is required."})

    if not new_description and not new_name:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": "One of Fields (NewName ot NewDescription) is required."})

    if not pyotp.TOTP(request.user.otp_key).verify(code, valid_window=1):
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Одноразовый пароль неверен, повторите Вашу попытку."})


    platforms = Platform.objects.filter(admin_id=user_id, admin=support_user)


    if platforms.exists():
        try:
            cur_platform = Platform.objects.select_for_update().get(uuid=platforms.first().uuid)

            if new_name:
                cur_platform.name = new_name

            if new_description:
                cur_platform.description = new_description

            cur_platform.save()

            data = PlatformSerializer(cur_platform).data

            data["ok"] = True
            data["message"] = "Платформа успешно изменена."

            return Response(status=status.HTTP_200_OK, data=data)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Произошла ошибка, попробуйте изменить данные еще раз."})

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": "Такой платформы не найдено."})
