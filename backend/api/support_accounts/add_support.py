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
def add_new_support(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        username = data.get('username', None)
        password = data.get('password', None)
        re_password = data.get('re_password', None)
        code = data.get('code', None)
        # invite = data.get('invite', None)
        try:
            admin = User.objects.get(id=request.user.id)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Произошла ошибка, попробуйте обновить страницу."})

        if not code:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Field code, code is required"})

        try:
            username = User.objects.get(username=username)
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Аккаунт с таким никнеймом уже существует."})
        except:
            pass

        if not pyotp.TOTP(admin.otp_key).verify(code, valid_window=1):
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Одноразовый пароль неверен, повторите Вашу попытку."})

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

        if re.match(password_pattern, password) is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"message": "Указанный пароль слишком прост"})


        with transaction.atomic():

            #
            # invite = InviteCode.objects.select_for_update().get(is_used=False, code=invite)

            user, create = User.objects.get_or_create(
                username=username,
                type="support",
                platform=Platform.objects.get(admin=admin)
            )


            # invite.is_used = True
            # invite.registered_user = user
            # invite.save()
            if create:
                user.groups.add(Group.objects.get(name='gramdesk_default_support'))
                user.username = username
                user.otp_key = pyotp.random_base32()
                user.set_password(password)
                user.save()

        supporters_array = []
        supporters = User.objects.filter(platform=admin.platform, type="support")

        for supp in supporters:
            if supp != admin:
                supporters_array.append({
                    "user_id": supp.id,
                    "username": supp.username,
                    "otp_url": supp.otp_key,
                    "otp_key": f'''otpauth://totp/Gramdesk: {supp.platform.name}?secret={supp.otp_key}''',
                    "isEditing": False,
                })

        return Response(status=status.HTTP_200_OK,
                        data={
                            "ok": True,
                            "message": "На вашу почту выслан код для регистрации.",
                            "username": user.username,
                            "user_id": user.id,
                            'otp_key': user.otp_key,
                            'url': f'''otpauth://totp/Gramdesk: {user.username}?secret={user.otp_key}''',
                            "supporters": supporters_array
                        })

    except IntegrityError:
        try:
            username = User.objects.get(username=username)
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Аккаунт с таким никнеймом уже существует."})
        except:
            pass



