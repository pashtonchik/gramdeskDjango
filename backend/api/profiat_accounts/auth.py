from rest_framework import status
from rest_framework.response import Response
import json
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from django.db.models import F
import logging
from backend.models import JWTToken, User
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework.decorators import api_view, permission_classes

from backend.permissions import ProfiatIntegration


@api_view(["POST"])
@transaction.atomic()
@permission_classes([ProfiatIntegration])
def profiat_auth_client(request):
    data = json.loads(request.body.decode("utf-8"))
    logger = logging.getLogger("mylogger")
    logger.info(data)
    try:
        username = data['username']
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": "Field Username is required"})

    try:
        profiat_id = data['id']
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": "Field Username is required"})

    try:
        profiat_email = data['email']
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": "Field Email is required"})

    client = User.objects.select_for_update().filter(profiat_id=profiat_id)

    if not client.exists():
        client = User(
            username=f"Profiat User {username}",
            profiat_id=profiat_id,
            profiat_username=username,
            profiat_email=profiat_email,
            type='client',
        )
        client.save()
    else:
        client = client.first()
        if client.profiat_email != profiat_email:
            client.profiat_email = profiat_email
        if client.profiat_username != username:
            client.profiat_username = username
            client.username = f"Profiat User {username}"

        client.save()


    refresh = RefreshToken.for_user(client)
    access = str(refresh.access_token)

    JWTToken.objects.create(
        user=client,
        jwt=access,
        refresh=OutstandingToken.objects.get(token=str(refresh))
    ).save()

    return Response(status=status.HTTP_200_OK, data={
        "ok": True,
        'refresh': str(refresh),
        'access': access,
        'message': 'Success',
    })


# @permission_classes([ProfiatDefaultUser])
@api_view(["POST"])
def verify_token(request):
    return Response(status=status.HTTP_200_OK, data={
        'ok': True,
        'message': 'JWT is valid'
    })
