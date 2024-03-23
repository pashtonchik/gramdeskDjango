import datetime

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.response import Response
import json
from rest_framework_simplejwt.tokens import RefreshToken
from backend.models import User, JWTToken, TelegramBot, Platform, Ticket
from django.contrib.auth.hashers import make_password
from django.db import transaction
import logging
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework.decorators import api_view
import pyotp
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from backend.serializers import TicketSerializer, TicketMessageSerializer


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
        username=f"Пользователь сайта {User.objects.filter(type='client').count() + 1}",
    )

    new_client.save()

    cur_ticket = Ticket(
        tg_user=new_client,
        status='created',
        platform=new_client.platform,
        source="widget",
        date_last_message=datetime.datetime.now(),

    )
    cur_ticket.save()

    refresh = RefreshToken.for_user(new_client)
    access = str(refresh.access_token)

    JWTToken.objects.create(
        user=new_client,
        jwt=access,
        refresh=OutstandingToken.objects.get(token=str(refresh))
    ).save()

    channel_layer = get_channel_layer()

    data = {
        'event': "incoming",
        'type': 'new_message',
        "new_ticket": TicketSerializer(cur_ticket, context={"from_user_type": "support"}).data,
    }

    async_to_sync(channel_layer.group_send)("active_support", {"type": "chat.message",
                                                  "message": json.dumps(data)})

    return Response(status=status.HTTP_200_OK, data={
        "ok": True,
        'access': access,
        "chat_id": str(cur_ticket.uuid),
        'message': 'Успешная регистрация.',
        'user_id': new_client.id,

    })
