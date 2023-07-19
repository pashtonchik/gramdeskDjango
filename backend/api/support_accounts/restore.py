from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import json
from dispatcher.models import User, DualFactorRequest, DefaultFee, FeeItem
from django.db import transaction
import re
from django.db.utils import IntegrityError
import pyotp
from datetime import datetime
from django.contrib.auth.hashers import make_password, check_password
from profiat.send_email_code import send_email_code_for_registration, send_email_code_for_restore
from django.contrib.auth.models import Group
from rest_framework.decorators import api_view, permission_classes
from dispatcher.permission import ProfiatDefaultUser
from django.db.models import F
from rest_framework_simplejwt.tokens import RefreshToken
import logging
from dispatcher.models import JWTToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken


@api_view(['POST'])
@transaction.atomic()
def restore(request):
    data = json.loads(request.body.decode("utf-8"))

    try:
        email = data['email']
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False,  "message" : "Field Password is required"})

    try:
        new_password = data['new_password']
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False,  "message" : "Field new_password is required"})

    try:
        re_new_password = data['re_new_password']
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False,  "message" : "Field re_new_password is required"})


    try:
        user = User.objects.select_for_update().get(my_email=email)

    except:
        return Response(status=status.HTTP_404_NOT_FOUND, data={"ok" : False, "message" : "Пользователь не найден."})

    code = data.get('code', None)
    
    password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$'

    if new_password != re_new_password:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, "message" : "Password not equal second password"})


    if re.match(password_pattern, new_password) is None:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"message" : "Указанный пароль слишком прост"})
        

    timestamp = int(datetime.now().timestamp())

    if not code:

        dfr = DualFactorRequest.objects.filter(timestamp__gte=timestamp - 120, user=user, action__in=['restore'], factor_type='email_auth', verified=False)

        if dfr.exists():    
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok" : False, 'message': 'Вы уже запросили код. Запросите новый через 2 минуты.'})
            
        send_email_code_for_restore.delay(user.my_email)

        return Response(status=status.HTTP_202_ACCEPTED, data={
            "ok" : True, 
            'message' : 'Введите код, высланный на Вашу почту для входа в аккаунт.',
            'email' : user.my_email
        })
    else:
        
        dfr = DualFactorRequest.objects.filter(timestamp__gte=timestamp - 600, user=user, action__in=['restore'], factor_type='email_auth', verified=False) 

        if dfr.filter(attempt__lte=0).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, 'message' : 'Вы израсходовали все попытки для ввода кода. Попробуйте снова через некоторое время.'})

        
        dfr_otp = DualFactorRequest.objects.filter(timestamp__gte=timestamp - 1800, user=user, action='restore', factor_type='email_auth', verified=False, otp=code)


        if dfr_otp.exists():

            otp = dfr_otp.first()
            otp.verified = True
            otp.save()
            refresh = RefreshToken.for_user(user)

            access = str(refresh.access_token)

            outstanding = JWTToken.objects.select_for_update().filter(user=user, active=True)
            outstanding.update(active=False)

            jwt_token = JWTToken.objects.create(
                user=user,
                jwt=access,
                refresh=OutstandingToken.objects.get(token=str(refresh))
            )
            jwt_token.save()

            token_mas = []
            for i in outstanding:
                token_mas.append(BlacklistedToken(token=i.refresh))
            user.set_password(new_password)
            user.save()
            BlacklistedToken.objects.bulk_create(token_mas, ignore_conflicts=True)
            return Response(status=status.HTTP_200_OK, data={
                'ok' : True, 
                'refresh': str(refresh),
                'access': access,
                'message' : 'Успешный вход',
                'username' : user.username,
                'id' : user.id
            })


        dfr.update(attempt=F('attempt') - 1)

        return Response(status=status.HTTP_404_NOT_FOUND, data={
            "ok" : False, 
            'message' : 'Введён неверный код авторизации.'
        })

