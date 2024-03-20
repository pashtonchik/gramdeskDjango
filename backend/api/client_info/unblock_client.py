import json
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from backend.models import Ticket, User
from backend.serializers import ClientSerializer


@transaction.atomic()
@api_view(['POST'])
def unblock_client(request):
    data = json.loads(request.body.decode("utf-8"))

    chat_id = data.get('chat_id')
    try:
        support_user = request.user
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": "Произошла ошибка, обновите страницу."})

    if not chat_id:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": "Field Chat_Id, Chat_Id is required."})

    try:

        chats = Ticket.objects.filter(uuid=chat_id, platform=support_user.platform)
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Пользователя не найдено."})


    if chats.exists():
        cur_user = User.objects.select_for_update().get(id=chats.first().tg_user.id)

        if not cur_user.is_blocked:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Пользователь не заблокирован."})

        cur_user.is_blocked = False
        cur_user.save()

        data = ClientSerializer(cur_user).data

        return Response(status=status.HTTP_200_OK, data=data)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": "Пользователя не найдено."})