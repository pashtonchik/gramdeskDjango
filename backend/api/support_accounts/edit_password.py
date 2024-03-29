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
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.db.models import F, Q
from django.db import transaction
import pyotp

from backend.models import User


@api_view(['POST'])
@transaction.atomic()
def edit_password(request):
    data = json.loads(request.body.decode("utf-8"))

    try:
        password = data['password']
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False,  "message" : "Field Password is required"})

    try:
        new_password = data['new_password']
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False,  "message" : "Field new_password is required"})

    try:
        re_new_password = data['re_new_password']
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False,  "message" : "Field re_new_password is required"})


    try:
        user = User.objects.select_for_update().get(username=request.user.username)

        if make_password(password, salt=user.password.split('$')[2]) != user.password:
            return Response(status=status.HTTP_404_NOT_FOUND, data={"ok" : False,  "message" : "Введён неверный старый пароль"})
    except:
        return Response(status=status.HTTP_404_NOT_FOUND, data={"ok" : False, "message" : "Введён неверный старый пароль"})

    code = data.get('code', None)
    
    password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$'

    if new_password != re_new_password:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, "message" : "Password not equal second password"})


    if re.match(password_pattern, new_password) is None:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"message" : "Указанный пароль слишком прост"})


    if not pyotp.TOTP(request.user.otp_key).verify(code, valid_window=1):
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Одноразовый пароль неверен, повторите Вашу попытку."})


    user.set_password(new_password)
    user.save()

    return Response(status=status.HTTP_200_OK, data={
        "ok": True,
        'message': 'Ваш пароль успешно изменен!',
        'username': user.username,
        'id': user.id
    })


