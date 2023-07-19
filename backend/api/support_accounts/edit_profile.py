from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import json
from rest_framework_simplejwt.tokens import RefreshToken
from dispatcher.models import User, DualFactorRequest, Payments, Notify
from datetime import datetime, timedelta
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Sum
from dispatcher.permission import ProfiatDefaultUser, permissions
from rest_framework.decorators import api_view, permission_classes
import re
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from profiat.send_email_code import send_email_code_for_edit_profile
from dispatcher.models import JWTToken
from django.db.models import F
from django.db import transaction


@api_view(['POST'])
@permission_classes([ProfiatDefaultUser])
@transaction.atomic()
def edit_profile_data(request):
    data = json.loads(request.body.decode("utf-8"))

    try:
        new_username = data['new_username']
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": "Field New Username is required"})


    try:
        user = User.objects.select_for_update().get(id=request.user.id)
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False, "message": "Попробуйте обновить страницу для изменения данных профиля."})

    if new_username:
        if user.username == new_username:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Вы указали текущее имя пользователя."})

        if User.objects.filter(username__iexact=new_username).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, "message": "Данное пользовательское имя уже используется, попробуйте выбрать другой ник."})



    code = data.get('code', None)

    timestamp = int(datetime.now().timestamp())

    if not code:
        dfr = DualFactorRequest.objects.filter(timestamp__gte=timestamp - 1800, user=user, action__in=['edit_profile'],
                                               factor_type='email_auth')

        if dfr.filter(verified=True).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, 'message': 'Вы изменяли пользовательское имя недавно, вы сможете его изменить снова только через некоторые время.'})
        dfr = dfr.filter(timestamp__gte=timestamp - 120, user=user, action__in=['edit_profile'],
                                               factor_type='email_auth', verified=False)

        if dfr.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok": False, 'message': 'Вы уже запросили код. Запросите новый через 2 минуты.'})

        send_email_code_for_edit_profile.delay(user.my_email)

        return Response(status=status.HTTP_202_ACCEPTED, data={
            "ok": True,
            'message': 'Введите код, высланный на Вашу почту для изменения данных профиля.',
            'email': user.my_email
        })
    else:

        dfr = DualFactorRequest.objects.filter(timestamp__gte=timestamp - 600, user=user, action__in=['edit_profile'],
                                               factor_type='email_auth', verified=False)

        if dfr.filter(attempt__lte=0).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False,
                                                                      'message': 'Вы израсходовали все попытки для ввода кода. Попробуйте снова через некоторое время.'})

        dfr_otp = DualFactorRequest.objects.filter(timestamp__gte=timestamp - 1800, user=user, action='edit_profile',
                                                   factor_type='email_auth', verified=False, otp=code)

        if dfr_otp.exists():
            otp = dfr_otp.first()
            otp.verified = True
            otp.save()

            user.username = new_username
            user.save()

            return Response(status=status.HTTP_200_OK, data={
                "ok": True,
                'message': 'Данные Вашего профиля успешно изменены',
            })

        dfr.update(attempt=F('attempt') - 1)

        return Response(status=status.HTTP_404_NOT_FOUND, data={
            "ok": False,
            'message': 'Введён неверный код авторизации.'
        })

