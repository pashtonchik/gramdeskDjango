from rest_framework import routers
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from backend.api.client_info.block_client import block_client
from backend.api.client_info.client_info import get_client
from backend.api.client_info.update_client import update_client_info
from backend.api.files.get_file import get_attachment
from backend.api.message_from_telegram.message_from_user import telegram
from backend.api.profiat_accounts.auth import profiat_auth_client
from backend.api.profiat_accounts.close_access import close_access
from backend.api.profiat_accounts.refresh import refresh as refresh_profiat
from backend.api.support_accounts.refresh import refresh as refresh_support
from backend.api.support_accounts.auth import auth, abc123
from backend.api.support_accounts.auth_verify import verify_token
from backend.api.support_accounts.restore import restore
from backend.api.support_accounts.signup import *
from backend.api.support_accounts.signup_new_code import registrate_req_new_code
from backend.permissions import ProfiatIntegration

router = routers.DefaultRouter()

urlpatterns = [
    # Profiat
    path('api/v2/client/auth/', profiat_auth_client),
    path('api/v2/client/auth/refresh/', refresh_profiat),
    path('api/v2/client/auth/close/access/', close_access),
    path('api/abc/', abc123),
    # Support
    path('api/v3/support/auth/', auth),
    path('api/v3/support/auth/verify/', verify_token),
    path('api/v3/support/auth/refresh/', refresh_support),

    path('api/file/download/<int:attachment>/', get_attachment),

    path('tg_bots/<str:token>', telegram),

    # Auth
    path('api/v3/support/signup/', registrate),
    path('api/v3/support/signup/verify/email/', registration_verify_email),
    path('api/v3/support/signup/connect/otp/', registration_enable_otp),
    path('api/v3/support/signup/reverify/email/', registrate_req_new_code),

    path('api/v3/support/restore/', restore),

    # Clients Management
    path('api/v3/support/update/client/', update_client_info),
    path('api/v3/support/block/client/', block_client),
    path('api/v3/support/get/client/', get_client),


] + router.urls
