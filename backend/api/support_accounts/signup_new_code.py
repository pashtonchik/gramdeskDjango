from rest_framework import status
from rest_framework.response import Response
import json
import pyotp
from backend.models import User, Platform, DualFactorRequest
from django.db import transaction
import re
from django.db.utils import IntegrityError
from datetime import datetime
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from rest_framework.decorators import api_view
from django.db.models import F
from rest_framework_simplejwt.tokens import RefreshToken
from tickets.background.auth.registration import send_email_code_for_registration


@api_view(["POST"])
def registrate_req_new_code(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        platform_name = data.get('platform_name', None)
        email = data.get('email', None)
        username = data.get('username', None)
        password = data.get('password', None)
        re_password = data.get('re_password', None)

        if not platform_name:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Field platform_name, platform_name is required"})
        if not email:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Field email, email is required"})
        if not username:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Field username, username is required"})
        if not password or not re_password:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Field password, password is required"})
        if password != re_password:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Password not equal second password"})

        password_pattern = "^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$"
        email_pattern = "(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"

        if re.match(password_pattern, password) is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"message": "Указанный пароль слишком прост"})

        if re.match(email_pattern, email) is None:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Указан неправильный e-mail."})

        with transaction.atomic():

            #
            # invite = InviteCode.objects.select_for_update().get(is_used=False, code=invite)

            user = User.objects.get(my_email=email)

            if make_password(password, salt=user.password.split('$')[2]) != user.password:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": f"Пароль не совпадает"})

            if username != user.username:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": f"Имя пользователя не совпадает"})

            timestamp = int(datetime.now().timestamp())
            dfr = DualFactorRequest.objects.filter(timestamp__gte=timestamp - 600, user=user, action__in=['registration'],
                                                   factor_type='email_auth', verified=False)

            last_dfr = dfr.order_by('-timestamp').first()

            if not last_dfr.timestamp + 120 <= timestamp:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={
                    "ok": False,
                    "message": "Еще не истекло время, через которое можно запросить код повторно."
                })

            transaction.on_commit(lambda: send_email_code_for_registration.delay(email))

        return Response(status=status.HTTP_200_OK,
                        data={"ok": True, "message": "На вашу почту выслан код для регистрации."})

    except IntegrityError:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={
            "ok": False,
            "message": "При регистрации произошла какая-то ошибка. Попробуйте зарегистрироваться через некоторое время."
        })