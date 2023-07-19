import pyotp as pyotp
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
import json
from rest_framework_simplejwt.tokens import RefreshToken
from dispatcher.models import User, DualFactorRequest, FeeItem, DefaultFee
from datetime import datetime
from django.contrib.auth.hashers import make_password, check_password

from dispatcher.permission import ProfiatDefaultUser
from profiat.send_email_code import send_email_code_for_login, send_email_code_for_registration
from django.db import transaction
from django.db.models import F
import logging
import hashlib
from dispatcher.models import JWTToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from dispatcher.serializers import MyTokenObtainPairSerializer
from profiat.send_sms_code import send_sms_code


# from rest_framework_simplejwt.models import

@api_view(["POST"])
@transaction.atomic()
@permission_classes([ProfiatDefaultUser])
def enable_2fa(request):
    data = json.loads(request.body.decode("utf-8"))
    logger = logging.getLogger("mylogger")
    logger.info(data)

    user = request.user

    code = data.get('code', None)
    try:
        auth_type = data['2fa_type']
    except KeyError:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={
            "ok": False,
            'message': 'Выбор типа аутентификации обязателен',
        })

    timestamp = int(datetime.now().timestamp())

    if user.otp_auth and auth_type == 'otp_auth':
        return Response(status=status.HTTP_400_BAD_REQUEST, data={
            "ok": False,
            'message': 'У вас уже подлючена OTP аутентификация',
        })

    if user.verify_phone and auth_type == 'sms_auth':
        return Response(status=status.HTTP_400_BAD_REQUEST, data={
            "ok": False,
            'message': 'У вас уже подлючена СМС аутентификация',
        })

    if not code:
        if auth_type == 'sms_auth':
            try:
                phone = data['phone_number']
            except KeyError:
                return Response(status=status.HTTP_400_BAD_REQUEST,
                                data={"ok": False, 'message': 'Поле номер телефона обязательно для заполнения.'})
            user.phone = phone
            user.sms_secret_key = pyotp.random_base32()
            dfr = DualFactorRequest.objects.filter(timestamp__gte=timestamp - 120, user=user,
                                                   action__in=['enable_2fa'], factor_type='sms_auth',
                                                   verified=False)

            if dfr.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST,
                                data={"ok": False, 'message': 'Вы уже запросили код для подключения СМС аутентификации. Запросите новый через 2 минуты.'})

            user.save()

            timestamp = int(datetime.timestamp(datetime.now()))
            dualReq = DualFactorRequest(
                factor_type='sms_auth',
                user=user,
                otp=str(pyotp.HOTP(user.sms_secret_key).at(timestamp)),
                timestamp=timestamp,
                action='enable_2fa'
            )
            dualReq.save()
            transaction.on_commit(lambda: send_sms_code(dualReq.id))

            return Response(status=status.HTTP_202_ACCEPTED, data={
                "ok": True,
                'message': 'Введите код, высланный на данный номер телефона для активации СМС аутентификации.',
                'phone': user.phone
            })
        elif auth_type == 'otp_auth':
            user.otp_secret_key = pyotp.random_base32()
            user.save()

            timestamp = int(datetime.timestamp(datetime.now()))
            dualReq = DualFactorRequest(
                factor_type='otp_auth',
                user=user,
                timestamp=timestamp,
                action='enable_2fa'
            )
            dualReq.save()
            return Response(status=status.HTTP_202_ACCEPTED, data={
                "ok": True,
                'message': 'Введите код, отображающийся в данный момент в вашем OTP-клиенте (Google Authenticator).',
                'otp_key': user.otp_secret_key,
                'url': f'''otpauth://totp/ProFiat?secret={user.otp_secret_key}'''
            })
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "ok": True,
                'message': 'Неизвестный тип аутентификации, попробуйте ещё раз.',
                'phone': user.phone
            })

    else:

        dfr = DualFactorRequest.objects.filter(timestamp__gte=timestamp - 600, user=user,
                                               action__in=['enable_2fa'], factor_type=auth_type,
                                               verified=False)

        if not dfr.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False,
                                                                      'message': 'Запроса на подключения двухфакторной аутентификации не найдено, попробуйте создать его заново.'})

        if dfr.filter(attempt__lte=0).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False,
                                                                      'message': 'Вы израсходовали все попытки для ввода кода. Попробуйте снова через некоторое время.'})


        dfr_otp = DualFactorRequest.objects.filter(timestamp__gte=timestamp - 1800, user=user, action='enable_2fa',
                                                   factor_type=auth_type, verified=False, otp=code)

        if dfr_otp.exists() or (pyotp.TOTP(user.otp_secret_key).verify(code, valid_window=1) and auth_type == 'otp_auth'):
            if auth_type == 'sms_auth':
                otp = dfr_otp.first()
                otp.verified = True
                otp.save()
                type_str = "СМС"
                user.verify_phone = True
            else:
                dfr.update(verified=True)
                type_str = "OTP"
                user.otp_auth = True
            user.save()
            return Response(status=status.HTTP_200_OK, data={
                "ok": True,
                'message': f'{type_str} аутентификация успешно подключена',
                'username': user.username,
                'id': user.id
            })

        dfr.update(attempt=F('attempt') - 1)

        return Response(status=status.HTTP_404_NOT_FOUND, data={
            "ok": False,
            'message': 'Введён неверный код авторизации.'
        })


@api_view(['POST'])
def disable_2fa(request):
    data = json.loads(request.body.decode("utf-8"))
    logger = logging.getLogger("mylogger")
    logger.info(data)

    user = request.user

    code = data.get('code', None)
    try:
        auth_type = data['2fa_type']
    except KeyError:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={
            "ok": False,
            'message': 'Выбор типа аутентификации обязателен',
        })

    timestamp = int(datetime.now().timestamp())

    if not user.otp_auth and auth_type == 'otp_auth':
        return Response(status=status.HTTP_400_BAD_REQUEST, data={
            "ok": False,
            'message': 'У вас уже отключена OTP аутентификация',
        })

    if not user.verify_phone and auth_type == 'sms_auth':
        return Response(status=status.HTTP_400_BAD_REQUEST, data={
            "ok": False,
            'message': 'У вас уже отключена СМС аутентификация',
        })

    if not code:
        if auth_type == 'sms_auth':
            try:
                phone = data['phone_number']
            except KeyError:
                return Response(status=status.HTTP_400_BAD_REQUEST,
                                data={"ok": False, 'message': 'Поле номер телефона обязательно для заполнения.'})
            user.phone = phone
            user.sms_secret_key = pyotp.random_base32()
            dfr = DualFactorRequest.objects.filter(timestamp__gte=timestamp - 120, user=user,
                                                   action__in=['disable_2fa'], factor_type='sms_auth',
                                                   verified=False)

            if dfr.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST,
                                data={"ok": False, 'message': 'Вы уже запросили код для подключения СМС аутентификации. Запросите новый через 2 минуты.'})

            user.save()

            timestamp = int(datetime.timestamp(datetime.now()))
            dualReq = DualFactorRequest(
                factor_type='sms_auth',
                user=user,
                otp=str(pyotp.HOTP(user.sms_secret_key).at(timestamp)),
                timestamp=timestamp,
                action='disable_2fa'
            )
            dualReq.save()
            transaction.on_commit(lambda: send_sms_code(dualReq.id))

            return Response(status=status.HTTP_202_ACCEPTED, data={
                "ok": True,
                'message': 'Введите код, высланный на данный номер телефона для активации СМС аутентификации.',
                'phone': user.phone
            })
        elif auth_type == 'otp_auth':
            user.otp_secret_key = pyotp.random_base32()
            user.save()

            timestamp = int(datetime.timestamp(datetime.now()))
            dualReq = DualFactorRequest(
                factor_type='otp_auth',
                user=user,
                timestamp=timestamp,
                action='disable_2fa'
            )
            dualReq.save()
            return Response(status=status.HTTP_202_ACCEPTED, data={
                "ok": True,
                'message': 'Введите код, отображающийся в данный момент в вашем OTP-клиенте (Google Authenticator).',
                'otp_key': user.otp_secret_key,
            })
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "ok": True,
                'message': 'Неизвестный тип аутентификации, попробуйте ещё раз.',
                'phone': user.phone
            })

    else:

        dfr = DualFactorRequest.objects.filter(timestamp__gte=timestamp - 600, user=user,
                                               action__in=['disable_2fa'], factor_type=auth_type,
                                               verified=False)

        if not dfr.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False,
                                                                      'message': 'Запроса на подключения двухфакторной аутентификации не найдено, попробуйте создать его заново.'})

        if dfr.filter(attempt__lte=0).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"ok": False,
                                                                      'message': 'Вы израсходовали все попытки для ввода кода. Попробуйте снова через некоторое время.'})


        dfr_otp = DualFactorRequest.objects.filter(timestamp__gte=timestamp - 1800, user=user, action='disable_2fa',
                                                   factor_type=auth_type, verified=False, otp=code)

        if dfr_otp.exists() or (pyotp.TOTP(user.otp_secret_key).verify(code, valid_window=1) and auth_type == 'otp_auth'):
            if auth_type == 'sms_auth':
                otp = dfr_otp.first()
                otp.verified = True
                otp.save()
                type_str = "СМС"
                user.verify_phone = False
            else:
                dfr.update(verified=True)
                type_str = "OTP"
                user.otp_auth = False
            user.save()
            return Response(status=status.HTTP_200_OK, data={
                "ok": True,
                'message': f'{type_str} аутентификация успешно отключена',
                'username': user.username,
                'id': user.id
            })

        dfr.update(attempt=F('attempt') - 1)

        return Response(status=status.HTTP_404_NOT_FOUND, data={
            "ok": False,
            'message': 'Введён неверный код авторизации.'
        })


@api_view(["GET"])
@transaction.atomic()
def get_2fa_states(request):
    logger = logging.getLogger("mylogger")

    user = request.user

    data = {
        'email': user.email,
        'id': user.id,
        'username': user.username,
        'email_auth': user.verify_email if user.my_email else False,
        'sms_auth': user.verify_phone if user.sms_secret_key else False,
        'otp_auth': user.otp_auth if user.otp_secret_key else False,
    }

    return Response(status=status.HTTP_200_OK, data=data)