from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.response import Response
import json
from rest_framework_simplejwt.tokens import RefreshToken
from backend.models import User, JWTToken
from django.contrib.auth.hashers import make_password
from django.db import transaction
import logging
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework.decorators import api_view
import pyotp
from decouple import config
import jwt


@api_view(["POST"])
@transaction.atomic()
def auth(request):
    data = json.loads(request.body.decode("utf-8"))
    logger = logging.getLogger("mylogger")
    logger.info(data) 
    try:
        username = data['username']
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, "message" : "Field Username is required"})

    try:
        code = data['otp']
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, "message" : "Field Otp is required"})

    try:
        password = data['password']
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False,  "message" : "Field Password is required"})

    # try:
    try:
        user = User.objects.select_for_update().get(username=username)
        print(user.password.split('$'))
        if make_password(password, salt=user.password.split('$')[2]) != user.password:
            return Response(status=status.HTTP_404_NOT_FOUND, data={"ok" : False,  "message" : "Неверный логин или пароль"})
        if not pyotp.TOTP(user.otp_key).verify(code, valid_window=1):
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Неверный одноразовый пароль (OTP)."})
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND, data={"ok": False, "message": "Неверный логин или пароль"})
    # except:
    #     return Response(status=status.HTTP_404_NOT_FOUND, data={"ok" : False, "message" : "Неверный логин или пароль"})

    refresh = RefreshToken.for_user(user)
    access = refresh.access_token

    decodeJTW = jwt.decode(str(access), config('SECRET_KEY'), algorithms=["HS256"]);

    # add payload here!!
    decodeJTW['username'] = 'tiago'
    decodeJTW['date'] = '2020-05-31'
    decodeJTW['platform_name'] = 'tiago'
    decodeJTW['id'] = 1

    # encode
    encoded = jwt.encode(decodeJTW, config('SECRET_KEY'), algorithm="HS256")

    JWTToken.objects.create(
        user=user,
        jwt=str(encoded),
        refresh=OutstandingToken.objects.get(token=str(refresh))
    ).save()

    return Response(status=status.HTTP_200_OK, data={
        "ok": True,
        'refresh': str(refresh),
        'access': access,
        'message': 'Успешный вход',
        'email': user.my_email,
        'username': user.username,
        'id': user.id,
        'platform_name': user.platform.name,
        'platform_description': user.platform.description,
        'supervisor': user == user.platform.admin,
    })



@api_view(["POST"])
@transaction.atomic()
def abc123(request):
    return Response(status=status.HTTP_200_OK, data={
        "ok": True,
    })