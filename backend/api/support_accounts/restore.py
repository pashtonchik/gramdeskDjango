from rest_framework import status
from rest_framework.response import Response
import json
from backend.models import User, DualFactorRequest
from django.db import transaction
import re
from datetime import datetime
from rest_framework.decorators import api_view, permission_classes
from django.db.models import F
from backend.models import JWTToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
import pyotp


@api_view(['POST'])
@transaction.atomic()
def restore(request):
    data = json.loads(request.body.decode("utf-8"))

    password = data.get('new_password', None)
    re_password = data.get('re_new_password', None)
    code = data.get('code', None)
    email = data.get('email', None)

    if not (password and re_password and code):

        try:
            email = data['email']
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": "Field Email is required"})

        try:
            user = User.objects.select_for_update().get(my_email=email)

        except:
            return Response(status=status.HTTP_404_NOT_FOUND, data={"ok": False, "message": "Пользователь не найден."})
        timestamp = int(datetime.timestamp(datetime.now()))

        dfr = DualFactorRequest.objects.filter(timestamp__gte=timestamp - 300, user=user, action__in=['restore'],
                                               factor_type='otp_auth', verified=False)

        if dfr.filter(attempt__lte=0).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False,
                                                                      'message': 'Вы недавно уже восстанавливали пароль, попробуйте через несколько минут.'})



        dualReq = DualFactorRequest(
            factor_type='otp_auth',
            user=user,
            timestamp=timestamp,
            action='restore'
        )
        dualReq.save()

        return Response(status=status.HTTP_200_OK, data={
            "ok": True,
            'message': 'Укажите новый пароль и OTP пароль для подтверждения личности.'
        })



    else:
        try:
            code = data['code']
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Field code is required"})
        try:
            new_password = data['new_password']
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Field new_password is required"})

        try:
            re_new_password = data['re_new_password']
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Field re_new_password is required"})

        try:
            user = User.objects.select_for_update().get(my_email=email)

        except:
            return Response(status=status.HTTP_404_NOT_FOUND, data={"ok": False, "message": "Пользователь не найден."})

        password_pattern = "^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$"

        if new_password != re_new_password:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Password not equal second password"})

        if re.match(password_pattern, new_password) is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"message": "Указанный пароль слишком прост"})

        timestamp = int(datetime.now().timestamp())

        dfr = DualFactorRequest.objects.filter(timestamp__gte=timestamp - 300, user=user, action__in=['restore'],
                                               factor_type='otp_auth', verified=False)

        if dfr.filter(attempt__lte=0).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False,
                                                                      'message': 'Вы израсходовали все попытки для ввода кода. Попробуйте снова через некоторое время.'})

        if pyotp.TOTP(user.otp_key).verify(code, valid_window=1):
            user.set_password(new_password)
            user.save()

            outstanding = JWTToken.objects.select_for_update().filter(user=user, active=True)
            outstanding.update(active=False)

            token_mas = []
            for i in outstanding:
                token_mas.append(BlacklistedToken(token=i.refresh))
            BlacklistedToken.objects.bulk_create(token_mas, ignore_conflicts=True)

            return Response(status=status.HTTP_200_OK, data={
                "ok": True,
                'message': 'Пароль успешно изменен, можете авторизироваться заново.',
            })

        dfr.update(attempt=F('attempt') - 1)

        return Response(status=status.HTTP_404_NOT_FOUND, data={
            "ok": False,
            'message': 'Введён неверный код авторизации.',
            "attempts": dfr.order_by('-timestamp').first().attempt - 1
        })

