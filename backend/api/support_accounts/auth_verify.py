from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from backend.permissions import GramDeskDefaultSupport


@api_view(["POST"])
@permission_classes([GramDeskDefaultSupport])
def verify_token(request):
    return Response(status=status.HTTP_200_OK, data={
        'ok': True,
        'message': 'JWT is valid',
    })