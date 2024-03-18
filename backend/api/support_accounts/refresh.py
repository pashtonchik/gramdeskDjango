from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.response import Response
import json
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime
from django.db import transaction
import logging
from backend.models import JWTToken, TelegramBot
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework.decorators import api_view


@api_view(["POST"])
@transaction.atomic()
def refresh(request):
    data = json.loads(request.body.decode("utf-8"))
    logger = logging.getLogger("mylogger")
    logger.info(data)

    try:
        refresh = data['refresh']
    except KeyError:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={'ok': False, 'message': "Field Refresh is required."})

    try:
        old_refresh = OutstandingToken.objects.select_for_update().get(token=str(refresh))
    except (OutstandingToken.MultipleObjectsReturned, ObjectDoesNotExist):
        return Response(status=status.HTTP_400_BAD_REQUEST, data={'ok': False, 'message': "Refresh already expired."})

    if old_refresh.expires_at.timestamp() <= datetime.now().timestamp():
        return Response(status=status.HTTP_400_BAD_REQUEST, data={'ok': False, 'message': "Refresh already expired."})

    if BlacklistedToken.objects.filter(token=old_refresh):
        return Response(status=status.HTTP_400_BAD_REQUEST, data={'ok': False, 'message': "Refresh is not valid."})

    if old_refresh.user.is_blocked:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={'ok': False, 'message': "Refresh is not valid."})

    if old_refresh.user.type != 'support':
        return Response(status=status.HTTP_400_BAD_REQUEST, data={'ok': False, 'message': "Refresh is not valid."})

    if not old_refresh.user.groups.filter(name='gramdesk_default_support').exists():
        return Response(status=status.HTTP_400_BAD_REQUEST, data={'ok': False, 'message': "Refresh is not valid."})

    logger.info(old_refresh.id)

    old_access = JWTToken.objects.select_for_update().filter(user=old_refresh.user, active=True, refresh=old_refresh)
    old_access.update(active=False)

    user = old_refresh.user
    logger.info(old_refresh.user.username)
    new_refresh = RefreshToken.for_user(user)
    new_access = str(new_refresh.access_token)

    JWTToken.objects.create(
        user=user,
        jwt=new_access,
        refresh=OutstandingToken.objects.get(token=str(new_refresh)),
        date_created=datetime.now().timestamp()
    ).save()

    BlacklistedToken(
        token=old_refresh,
    ).save()

    return Response(status=status.HTTP_200_OK, data={
        "ok": True,
        'refresh': str(new_refresh),
        'access': new_access,
        'email': user.my_email,
        'username': user.username,
        'id': user.id,
        'platform_name': user.platform.name,
        'platform_description': user.platform.description,
        'supervisor': user == user.platform.admin,
        'tg_bot': TelegramBot.objects.filter(platform=user.platform).exists()
    })