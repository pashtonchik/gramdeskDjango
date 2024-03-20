from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.response import Response
import json
from rest_framework_simplejwt.tokens import RefreshToken
from backend.models import User, JWTToken, TelegramBot, Platform
from django.contrib.auth.hashers import make_password
from django.db import transaction
import logging
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework.decorators import api_view
import pyotp


@api_view(["POST"])
@transaction.atomic()
def widget_client_auth(request):
    data = json.loads(request.body.decode("utf-8"))
    logger = logging.getLogger("mylogger")
    logger.info(data)
    try:
        platform = data['platform']
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, "message" : "Field Platform is required"})

    new_client = User(
        type="client",
        source="widget",
        platform=Platform.objects.get(uuid=platform),
        username=f"Пользователь сайта{User.objects.count() + 1}",
    )

    new_client.save()

    refresh = RefreshToken.for_user(new_client)
    access = str(refresh.access_token)

    JWTToken.objects.create(
        user=new_client,
        jwt=access,
        refresh=OutstandingToken.objects.get(token=str(refresh))
    ).save()

    return Response(status=status.HTTP_200_OK, data={
        "ok": True,
        'access': access,
        'message': 'Успешная регистрация.',
    })
