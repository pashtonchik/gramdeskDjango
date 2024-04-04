from rest_framework import status
from rest_framework.response import Response
import json
import pyotp
from backend.models import User, Platform, DualFactorRequest
from django.db import transaction
import re
from django.db.utils import IntegrityError
from datetime import datetime
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from rest_framework.decorators import api_view
from django.db.models import F
from rest_framework_simplejwt.tokens import RefreshToken
from tickets.background.auth.registration import send_email_code_for_registration


@api_view(["POST"])
def delete_support(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        user_id = data.get('user_id', None)
        code = data.get('code', None)

        # invite = data.get('invite', None)
        try:
            admin = User.objects.get(id=request.user.id)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Произошла ошибка, попробуйте обновить страницу."})
        if not user_id:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Field IserId, UserId is required"})
        if not code:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Field code, code is required"})



        with transaction.atomic():

            #
            # invite = InviteCode.objects.select_for_update().get(is_used=False, code=invite)

            users = User.objects.filter(id=user_id, platform=admin.platform)
            if not users.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST,
                                data={
                                    "ok": False,
                                    "message": "Пользователя с таким идентификатором не существует.",
                                })

            user = users.first()

            if not pyotp.TOTP(admin.otp_key).verify(code, valid_window=1):
                return Response(status=status.HTTP_400_BAD_REQUEST,
                                data={"ok": False, "message": "Одноразовый пароль неверен, повторите Вашу попытку."})
            old_id = user.id
            user.delete()

            supporters_array = []
            supporters = User.objects.filter(platform=admin.platform, type="support")

            for supp in supporters:
                if supp != admin:
                    supporters_array.append({
                        "user_id": supp.id,
                        "username": supp.username,
                        "otp_url": supp.otp_key,
                        "otp_key": f'''otpauth://totp/Gramdesk: {supp.platform.name}?secret={supp.otp_key}''',
                        "isEditing": False,
                    })

            return Response(status=status.HTTP_200_OK, data={
                "ok": True,
                'message': 'Сотрудник поддержки успешно удален!',
                "user_id": old_id,
                "supporters": supporters_array
            })
    except Exception as e:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Произошла непредвиденная ошибка, повторите вашу попытку позже."})




