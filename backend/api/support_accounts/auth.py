from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import json
from rest_framework_simplejwt.tokens import RefreshToken
from dispatcher.models import User, DualFactorRequest, FeeItem, DefaultFee, Activity
from datetime import datetime
from django.contrib.auth.hashers import make_password, check_password
from profiat.send_email_code import send_email_code_for_login, send_email_code_for_registration
from django.db import transaction
from django.db.models import F
import logging
import hashlib
from dispatcher.models import JWTToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from dispatcher.serializers import MyTokenObtainPairSerializer
# from rest_framework_simplejwt.models import 
from dispatcher.permission import ProfiatDefaultUser
from rest_framework.decorators import api_view, permission_classes


@api_view(["POST"])
@transaction.atomic()
def auth(request):
    data = json.loads(request.body.decode("utf-8"))
    logger = logging.getLogger("mylogger")
    logger.info(data) 
    try:
        username = data['username']
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, "message" : "Field Username is required"})

    try:
        password = data['password']
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False,  "message" : "Field Password is required"})

    try:
        user = User.objects.select_for_update().get(username=username)

        if make_password(password, salt=user.password.split('$')[2]) != user.password:
            return Response(status=status.HTTP_404_NOT_FOUND, data={"ok" : False,  "message" : "Неверный логин или пароль"})
    except:
        return Response(status=status.HTTP_404_NOT_FOUND, data={"ok" : False, "message" : "Неверный логин или пароль"})

    code = data.get('code', None)
    
    timestamp = int(datetime.now().timestamp())

    if not code:

        dfr = DualFactorRequest.objects.filter(timestamp__gte=timestamp - 120, user=user, action__in=['registrate', 'login'], factor_type='email_auth', verified=False)

        if dfr.exists():    
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"ok" : False, 'message': 'Вы уже запросили код. Запросите новый через 2 минуты.'})
            
        if user.verify_email:
            send_email_code_for_login.delay(user.my_email)

            return Response(status=status.HTTP_202_ACCEPTED, data={
                "ok" : True, 
                'message' : 'Введите код, высланный на Вашу почту для входа в аккаунт.',
                'email' : user.my_email
            })
        else:
            send_email_code_for_registration(user.my_email)

            return Response(status=status.HTTP_202_ACCEPTED, data={
                "ok" : True, 
                'message' : 'Введите код, высланный на Вашу почту для подтверждения аккаунта',
                'email' : user.my_email
            })
    else:
        
        dfr = DualFactorRequest.objects.filter(timestamp__gte=timestamp - 600, user=user, action__in=['registrate', 'login'], factor_type='email_auth', verified=False) 

        if dfr.filter(attempt__lte=0).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, 'message' : 'Вы израсходовали все попытки для ввода кода. Попробуйте снова через некоторое время.'})

        if user.verify_email:
            action = 'login'
        else:
            action = 'registrate'
        
        dfr_otp = DualFactorRequest.objects.filter(timestamp__gte=timestamp - 1800, user=user, action=action, factor_type='email_auth', verified=False, otp=code)


        if dfr_otp.exists():

            otp = dfr_otp.first()
            otp.verified = True
            otp.save()
            if action == 'registrate':
                user.verify_email = True
                user.save()
                for fee_objects in DefaultFee.objects.all():
                    if not FeeItem.objects.filter(user=user, direction=fee_objects.direction, paymethod=fee_objects.paymethod).exists():
                        FeeItem(
                            user=user,
                            direction=fee_objects.direction,
                            paymethod=fee_objects.paymethod,
                            percent_before=fee_objects.percent_before,
                            percent_after=fee_objects.percent_after,
                            limit_amount=fee_objects.limit_amount,
                        ).save()
            
            
            user.set_password(password)
            user.save()

            refresh = RefreshToken.for_user(user)
            access = str(refresh.access_token)

            JWTToken.objects.create(
                user=user,
                jwt=access,
                refresh=OutstandingToken.objects.get(token=str(refresh))
            ).save()

            Activity(
                user=user,
                type='system',
                text=f'Совершен вход в аккаунт.',
            ).save()

            return Response(status=status.HTTP_200_OK, data={
                "ok" : True, 
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

@permission_classes([ProfiatDefaultUser])
@api_view(["POST"])
def verify_token(request):
    return Response(status=status.HTTP_200_OK, data={
        'ok' : True,
        'message' : 'JWT is valid'
    })
