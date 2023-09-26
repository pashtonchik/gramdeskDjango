from rest_framework import generics
from rest_framework_simplejwt.views import TokenRefreshView

from backend.permissions import ProfiatIntegration


class UserView(TokenRefreshView):
    ...
    permission_classes = (ProfiatIntegration, )