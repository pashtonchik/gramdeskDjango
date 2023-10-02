import base64
import logging

import rsa
from rest_framework import permissions

from backend.models import JWTToken
from tickets.settings import PROFIAT_PUBKEY, pub_key_jwt


class ProfiatIntegration(permissions.BasePermission):
    def has_permission(self, request, view):
        # try:
        print(request.headers)
        # logger.info(request.headers)
        # logger.info(request.body)
        sign = request.headers.get('X-Token-Sign')

        message = request.method + '\n' + request.body.decode()

        # logger.info(message)

        rsa.verify(message.encode(), base64.b64decode(sign), PROFIAT_PUBKEY)
        return True
        # except:
        #     print('govno')
        #     return False


class GramDeskDefaultSupport(permissions.BasePermission):
    def has_permission(self, request, view):
        token = ''
        bearer = ''
        print(request.user)
        logger = logging.getLogger("mylogger")
        logger.info(request.headers)

        if not request.headers.get('Authorization'):
            return False

        bearer, token = request.headers.get('Authorization').split()
        print(token)
        if not token:
            return False
        if not JWTToken.objects.filter(jwt=token, active=True).exists():
            return False

        import jwt
        jwt_info = jwt.decode(token, pub_key_jwt, algorithms=["RS512"])
        logger.info(jwt_info)
        if request.user.is_blocked:
            return False

        if request.user.type != 'support':
            return False
        if request.user.groups.filter(name='gramdesk_default_support').exists():
            return True
        return False