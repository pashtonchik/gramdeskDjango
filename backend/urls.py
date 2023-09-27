from rest_framework import routers
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from backend.api.files.get_file import get_attachment
from backend.api.message_from_telegram.message_from_user import new_message
from backend.api.profiat_accounts.auth import profiat_auth_client
from backend.api.profiat_accounts.close_access import close_access
from backend.api.profiat_accounts.refresh import refresh as refresh_profiat
from backend.api.support_accounts.refresh import refresh as refresh_support
from backend.api.support_accounts.auth import auth
from backend.api.support_accounts.auth_verify import verify_token
from backend.permissions import ProfiatIntegration

router = routers.DefaultRouter()

urlpatterns = [
    # Profiat
    path('api/v2/client/auth/', profiat_auth_client),
    path('api/v2/client/auth/refresh/', refresh_profiat),
    path('api/v2/client/auth/close/access/', close_access),

    # Support
    path('api/v3/support/auth/', auth),
    path('api/v2/support/auth/verify/', verify_token),
    path('api/v2/support/auth/refresh/', refresh_support),


] + router.urls
