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
def registrate(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        platform_name = data.get('platform_name', None)
        email = data.get('email', None)
        username = data.get('username', None)
        password = data.get('password', None)
        re_password = data.get('re_password', None)
        # invite = data.get('invite', None)
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

            user, create = User.objects.get_or_create(
                my_email=email,
            )

            if not create:
                if not user.verify_email:
                    user.username = username
                    user.set_password(password)
                    user.save()
                    transaction.on_commit(lambda: send_email_code_for_registration.delay(email))
                    return Response(status=status.HTTP_200_OK,
                                data={"ok": True, "message": "Вы уже начинали регистрацию, на вашу почту заново выслан код для регистрации."})
                else:
                    user.username = username
                    user.set_password(password)
                    user.save()
                    return Response(status=status.HTTP_202_ACCEPTED,
                                    data={"ok": True,
                                          "message": "Вы уже начинали регистрацию, вам необходимо привязать OTP аутентификацию."})
                else:
                    return Response(status=status.HTTP_400_BAD_REQUEST,
                                data={"ok": False, "message": "Этот e-mail уже занят."})

            # invite.is_used = True
            # invite.registered_user = user
            # invite.save()
            if create:
                user.groups.add(Group.objects.get(name='gramdesk_default_support'))
                user.username = username
                user.set_password(password)
                user.save()
                transaction.on_commit(lambda: send_email_code_for_registration.delay(email))

        return Response(status=status.HTTP_200_OK,
                        data={"ok": True, "message": "На вашу почту выслан код для регистрации."})

    except IntegrityError:
        try:
            username = User.objects.get(username=username)
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Аккаунт с таким никнеймом уже существует."})
        except:
            pass
        try:
            user = User.objects.get(my_email=email)
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Пользователь с таким e-mail уже существует."})
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False,
                                                                      "message": "При регистрации произошла какая-то ошибка. Попробуйте зарегистрироваться через некоторое время."})


@transaction.atomic()
@api_view(['POST'])
def registration_verify_email(request):
    data = json.loads(request.body.decode("utf-8"))
    platform_name = data.get('platform_name', None)
    email = data.get('email', None)
    username = data.get('username', None)
    password = data.get('password', None)
    code = data.get('email_code', None)

    if not platform_name:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Field platform_name, platform_name is required"})
    if not email:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Field email, email is required"})
    if not username:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Field username, username is required"})
    if not password:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Field password, password is required"})
    if not code:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Field email_code, email_code is required"})

    try:
        user = User.objects.select_for_update().get(my_email=email)
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Заявки на регистрацию этого пользователя не найдено"})

    if user.username != username or make_password(password, salt=user.password.split('$')[2]) != user.password:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": f""})

    timestamp = int(datetime.now().timestamp())

    dfr = DualFactorRequest.objects.filter(timestamp__gte=timestamp - 600, user=user, action__in=['registrate'],
                                           factor_type='email_auth', verified=False)

    if dfr.filter(attempt__lte=0).exists():
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False,
                                                                  'message': 'Вы израсходовали все попытки для ввода кода. Запросите код через 2 минуты.'})

    dfr_otp = DualFactorRequest.objects.filter(timestamp__gte=timestamp - 300, user=user, action='registration',
                                               factor_type='email_auth', verified=False, otp=code)

    if dfr_otp.exists():
        user.verify_email = True
        otp = dfr_otp.first()
        otp.verified = True
        otp.save()
        user.otp_secret_key = pyotp.random_base32()
        user.save()

        timestamp = int(datetime.timestamp(datetime.now()))
        dualReq = DualFactorRequest(
            factor_type='otp_auth',
            user=user,
            timestamp=timestamp,
            action='registration'
        )
        dualReq.save()


        # refresh = RefreshToken.for_user(user)
        return Response(status=status.HTTP_200_OK, data={
            "ok": True,
            'message': 'Ваш Email подвтержден. Далее необходимо привязать OTP.',
            # 'refresh': str(refresh),
            # 'access': str(refresh.access_token),
            'username': user.username,
            'id': user.id,
            'otp_key': user.otp_secret_key,
            'url': f'''otpauth://totp/Gramdesk: {user.my_email}?secret={user.otp_secret_key}'''
        })

    dfr.update(attempt=F('attempt') - 1)

    return Response(status=status.HTTP_404_NOT_FOUND, data={"ok": False, 'message': 'Неверный код'})


@transaction.atomic()
@api_view(['POST'])
def registration_enable_otp(request):
    data = json.loads(request.body.decode("utf-8"))
    platform_name = data.get('platform_name', None)
    email = data.get('email', None)
    username = data.get('username', None)
    password = data.get('password', None)
    code = data.get('otp_code', None)

    if not platform_name:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Field platform_name, platform_name is required"})
    if not email:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Field email, email is required"})
    if not username:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Field username, username is required"})
    if not password:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Field password, password is required"})
    if not code:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Field otp_code, otp_code is required"})



    try:
        user = User.objects.select_for_update().get(my_email=email)
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"ok": False, "message": "Заявки на регистрацию этого пользователя не найдено"})

    if user.username != username or make_password(password, salt=user.password.split('$')[2]) != user.password:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": f"Пароль не верен."})

    timestamp = int(datetime.now().timestamp())

    dfr = DualFactorRequest.objects.filter(timestamp__gte=timestamp - 600, user=user, action='registration',
                                           factor_type='otp_auth', verified=False)

    if not dfr.exists():
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False,
                                                                  'message': f'Запроса на подключения двухфакторной аутентификации не найдено, попробуйте создать его заново.'})

    if dfr.filter(attempt__lte=0).exists():
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False,
                                                                  'message': 'Вы израсходовали все попытки для ввода кода. Попробуйте снова через некоторое время.'})

    if pyotp.TOTP(user.otp_key).verify(code, valid_window=1):

        user.enable_otp = True
        user.save()

        Platform(
            admin=user,
            name=platform_name,
        ).save()


        refresh = RefreshToken.for_user(user)
        return Response(status=status.HTTP_200_OK, data={
            "ok": True,
            'message': 'Регистрация прошла успешно',
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'username': user.username,
            'id': user.id
        })

    dfr.update(attempt=F('attempt') - 1)

    return Response(status=status.HTTP_404_NOT_FOUND, data={"ok": False, 'message': 'Неверный код'})
