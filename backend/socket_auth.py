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

        return token.user, token, token.user.platform
    except Exception:
        return AnonymousUser(), None


class TokenAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        headers = dict(scope['headers'])
        print(headers, b'authorization' in headers)

        path = scope['path']
        segments = path.strip('/').split('/')
        try:
            jwt = segments[1]
        except:
            scope['user'], scope['jwt'], scope['platform'] = AnonymousUser()

        if jwt:
            try:
                scope['user'], scope['jwt'], scope['platform'] = await get_user(jwt)
            except JWTToken.DoesNotExist:
                scope['user'], scope['jwt'], scope['platform'] = AnonymousUser()
        print(scope['user'])

        return await self.inner(scope, receive, send)