import json
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from backend.models import Ticket, User
from backend.serializers import ClientSerializer


@transaction.atomic()
@api_view(['POST'])
def update_client_info(request):
    data = json.loads(request.body.decode("utf-8"))

    chat_id = data.get('chat_id')
    new_username = data.get('new_username')
    new_description = data.get('new_description')
    try:
        support_user = request.user
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Произошла ошибка, обновите страницу."})

    if not chat_id:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": "Field Chat_Id, Chat_Id is required."})

    if not new_description and not new_username:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": "One of Fields (NewUsername ot NewDescription) is required."})

    try:

        chats = Ticket.objects.filter(uuid=chat_id, platform=support_user.platform)
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Пользователя не найдено."})


    if chats.exists():
        # try:
        cur_user = User.objects.select_for_update().get(id=chats.first().tg_user.id)

        if new_username:
            cur_user.username = new_username

        if new_description:
            cur_user.description = new_description
        cur_user.save()

        data = ClientSerializer(cur_user).data

        data["ok"] = True
        data["message"] = "Данные успешно изменены."

        return Response(status=status.HTTP_200_OK, data=data)
        # except:
        #     return Response(status=status.HTTP_400_BAD_REQUEST,
        #                     data={"ok": False, "message": "Произошла ошибка, попробуйте изменить данные еще раз."})

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": "Пользователя не найдено."})
