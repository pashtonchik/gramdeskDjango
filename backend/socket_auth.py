from asgiref.sync import sync_to_async
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser

from backend.models import JWTToken


@database_sync_to_async
def get_user(token_key):
    try:
        token = JWTToken.objects.get(jwt=token_key)
        return token.user
    except JWTToken.DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    """
    Token authorization middleware for Django Channels 2
    """

    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        headers = dict(scope['headers'])
        if b'authorization' in headers:
            try:
                token_name, token_key = headers[b'authorization'].decode().split()
                if token_name == 'Token':
                    scope['user'] = await get_user(token_key)
                    scope['jwt'] = JWTToken.objects.get(jwt=token_key)
            except JWTToken.DoesNotExist:
                scope['user'] = AnonymousUser()
            print(scope['user'])
        return await self.inner(scope, receive, send)