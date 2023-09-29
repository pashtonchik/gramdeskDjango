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
        password = data['password']
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False,  "message" : "Field Password is required"})

    # try:
    user = User.objects.select_for_update().get(username=username)
    print(user.password.split('$'))
    if make_password(password, salt=user.password.split('$')[2]) != user.password:
        return Response(status=status.HTTP_404_NOT_FOUND, data={"ok" : False,  "message" : "Неверный логин или пароль"})
    # except:
    #     return Response(status=status.HTTP_404_NOT_FOUND, data={"ok" : False, "message" : "Неверный логин или пароль"})

    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)

    JWTToken.objects.create(
        user=user,
        jwt=access,
        refresh=OutstandingToken.objects.get(token=str(refresh))
    ).save()

    return Response(status=status.HTTP_200_OK, data={
        "ok": True,
        'refresh': str(refresh),
        'access': access,
        'message': 'Успешный вход',
        'username': user.username,
        'id': user.id
    })



@api_view(["POST"])
@transaction.atomic()
def abc123(request):
    return Response(status=status.HTTP_200_OK, data={
        "ok": True,
    })