from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import json
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime, timedelta
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Sum
from rest_framework.decorators import api_view, permission_classes
import re
import pyotp
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from django.db.models import F
from django.db import transaction

from backend.models import User


@api_view(['POST'])
@transaction.atomic()
def edit_profile_data(request):
    data = json.loads(request.body.decode("utf-8"))

    try:
        new_support_name = data['new_support_name']
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": "Field New Username is required"})


    try:
        user = User.objects.select_for_update().get(id=request.user.id)
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": "Попробуйте обновить страницу для изменения данных профиля."})

    if new_support_name:
        if user.support_name == new_support_name:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Вы указали текущее имя пользователя."})

    code = data.get('code', None)

    if not pyotp.TOTP(request.user.otp_key).verify(code, valid_window=1):
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Одноразовый пароль неверен, повторите Вашу попытку."})

    user.support_name = new_support_name
    user.save()

    return Response(status=status.HTTP_200_OK, data={
        "ok": True,
        'message': 'Данные Вашего профиля успешно изменены.',
    })


