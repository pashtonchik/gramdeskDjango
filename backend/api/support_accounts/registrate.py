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
from profiat.send_email_code import send_email_code_for_registration
from django.contrib.auth.models import Group
from rest_framework.decorators import api_view, permission_classes
from dispatcher.permission import ProfiatDefaultUser
from django.db.models import F
from rest_framework_simplejwt.tokens import RefreshToken
import logging

# @transaction.atomic()
@api_view(["POST"])
def registrate(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        email = data.get('email', None)
        username = data.get('username', None)
        password = data.get('password', None)
        re_password = data.get('re_password', None)
        logger = logging.getLogger("mylogger")
        logger.info(data)  
        if not email:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, "message" : "Field email, email is required"})
        if not username:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, "message" : "Field username, username is required"})
        if not password or not re_password:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, "message" : "Field password, password is required"})
        if password != re_password:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, "message" : "Password not equal second password"})

        password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$'
        email_pattern = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        

        if re.match(password_pattern, password) is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"message" : "Указанный пароль слишком прост"})
        
        if re.match(email_pattern, email) is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, "message" : "Указан неправильный e-mail."})

        with transaction.atomic():
            user, create = User.objects.get_or_create(
                my_email=email,
            )


            if not create:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, "message" : "Этот e-mail уже занят."}) 


            if create:
                user.groups.add(Group.objects.get(name='profiat_default_user'))
                user.username = username
                user.set_password(password)
                user.save()
                transaction.on_commit(lambda: send_email_code_for_registration.delay(email))

        return Response(status=status.HTTP_200_OK, data={"ok" : True, "message" : "На вашу почту выслан код для регистрации."}) 
    except IntegrityError:
        try:
            username = User.objects.get(username=username)
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, "message" : "Аккаунт с таким никнеймом уже существует."})
        except:
            pass
        try:
            user = User.objects.get(my_email=email)
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, "message" : "Пользователь с таким e-mail уже существует."})
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, "message" : "При регистрации произошла какая-то ошибка. Попробуйте зарегистрироваться через некоторое время."})


@transaction.atomic()
@api_view(['POST'])
def continue_registration(request):
    data = json.loads(request.body.decode("utf-8"))

    email = data.get('email', None)
    username = data.get('username', None)
    password = data.get('password', None)
    code = data.get('code', None)

    if not email:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, "message" : "Field email, email is required"})
    if not username:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, "message" : "Field username, username is required"})
    if not password:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, "message" : "Field password, password is required"})
    if not code:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, "message" : "Field code, code is required"})
    
    try:
        user = User.objects.select_for_update().get(my_email=email)
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, "message" : "Заявки на регистрацию этого пользователя не найдено"})

    if user.username != username or make_password(password, salt=user.password.split('$')[2]) != user.password:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, "message" : f""})

    timestamp = int(datetime.now().timestamp())
    
    dfr = DualFactorRequest.objects.filter(timestamp__gte=timestamp - 600, user=user, action__in=['registrate'], factor_type='email_auth', verified=False) 

    if dfr.filter(attempt__lte=0).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok" : False, 'message' : 'Вы израсходовали все попытки для ввода кода. Запросите код через 2 минуты.'})


    dfr_otp = DualFactorRequest.objects.filter(timestamp__gte=timestamp - 300, user=user, action='registration', factor_type='email_auth', verified=False, otp=code)



    if dfr_otp.exists():
        user.verify_email = True
        otp = dfr_otp.first()
        otp.verified = True
        otp.save()
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
        refresh = RefreshToken.for_user(user)
        return Response(status=status.HTTP_200_OK, data={
            "ok" : True, 
            'message' : 'Регистрация прошла успешно',
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'username' : user.username,
            'id' : user.id
            })
    
    dfr.update(attempt=F('attempt') - 1)


    return Response(status=status.HTTP_404_NOT_FOUND, data={"ok" : False, 'message' : 'Неверный код'})
