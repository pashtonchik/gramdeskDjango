from asgiref.sync import sync_to_async
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser

from backend.models import JWTToken


@database_sync_to_async
def get_user(token_key):
    try:
        token = JWTToken.objects.all().first()
        return token.user, token
    except JWTToken.DoesNotExist:
        return AnonymousUser(), None



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
                    scope['user'], scope['jwt'] = await get_user(token_key)
            except JWTToken.DoesNotExist:
                scope['user'], scope['jwt'] = AnonymousUser()
            print(scope['user'])

        scope['user'], scope['jwt'] = await get_user(123)
        return await self.inner(scope, receive, send)