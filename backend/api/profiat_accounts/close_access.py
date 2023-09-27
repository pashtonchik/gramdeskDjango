from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import status
from rest_framework.response import Response
import json
from django.db import transaction
import logging
from backend.models import JWTToken, SocketConnection, User
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework.decorators import api_view, permission_classes


@api_view(["POST"])
@transaction.atomic()
def close_access(request):
    data = json.loads(request.body.decode("utf-8"))
    logger = logging.getLogger("mylogger")
    logger.info(data)

    try:
        profiat_id = data['id']
    except KeyError:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={'ok': False, 'message': "Field Refresh is required."})


    current_user = User.objects.filter(profiat_id=profiat_id)
    if current_user.count() != 1:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={'ok': False, 'message': "User does not exists."})
    else:
        current_user = current_user.first()

    sockets_for_close = SocketConnection.objects.select_for_update().filter(user=current_user, active=True)
    jwt_to_close = JWTToken.objects.select_for_update().filter(user=current_user, active=True)

    token_mas = []
    for i in jwt_to_close:
        BlacklistedToken(
            token=i.refresh,
        ).save()

    jwt_to_close.update(active=False)
    logger.info(123)
    #     token_mas.append(BlacklistedToken(token=i.refresh))
    # BlacklistedToken.objects.bulk_create(token_mas)

    channel_layer = get_channel_layer()
    for connection in sockets_for_close:
        async_to_sync(channel_layer.group_add)(f'close_access', connection.channel_name)

    async_to_sync(channel_layer.group_send)("close_access", {"type": "disconnect.by.heartbeat",
                                                                   "message": "disconnect"})

    sockets_for_close.update(active=False)

    return Response(status=status.HTTP_200_OK, data={"ok": True})