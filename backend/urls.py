from rest_framework import routers
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from backend.api.files.get_file import get_attachment
from backend.api.message_from_telegram.message_from_user import new_message
from backend.api.profiat_accounts.auth import profiat_auth_client
from backend.api.profiat_accounts.close_access import close_access
from backend.api.profiat_accounts.refresh import refresh
from backend.permissions import ProfiatIntegration

router = routers.DefaultRouter()

urlpatterns = [
    path('api/v2/client/auth/', profiat_auth_client),
    path('api/v2/client/auth/refresh/', refresh),
    path('api/v2/client/auth/close/access/', close_access),

    # Enable 2FA
    path('api/v1/new/message/', new_message),
    path('api/v3/get/attachement/<int:attachment>/', get_attachment)

] + router.urls
