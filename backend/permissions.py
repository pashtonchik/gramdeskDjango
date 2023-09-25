import base64

import rsa
from rest_framework import permissions


class ProfiatIntegration(permissions.BasePermission):
    def has_permission(self, request, view):
        try:

            # logger.info(request.headers)
            # logger.info(request.body)
            sign = request.headers.get('X-Token-Sign')

            message = request.method + '\n' + request.body.decode()

            # logger.info(message)

            rsa.verify(message.encode(), base64.b64decode(sign), PROFIAT_PUBKEY)
            return True
        except:
            return False