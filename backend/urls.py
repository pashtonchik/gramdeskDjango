from rest_framework import routers
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from backend.api.files.get_file import get_attachment
from backend.api.message_from_telegram.message_from_user import new_message
from backend.api.profiat_accounts.auth import profiat_auth_client
from backend.permissions import ProfiatIntegration

router = routers.DefaultRouter()

urlpatterns = [
    path('api/v2/client/auth/', profiat_auth_client),
    # path('api/v2/client/auth/refresh/', UserView.as_view()),
    # path('api/v3/accounts/auth/', auth),
    # path('api/v3/accounts/auth/refresh/', TokenRefreshView.as_view()),
    # path('api/v3/accounts/signup/', registrate),
    # path('api/v3/accounts/signup/action/', continue_registration),
    # path('api/v3/accounts/edit/password/', edit_password),
    # path('api/v3/accounts/restore/', restore),
    # path('api/v3/accounts/wallet/connect/', connect_flex),
    # path('api/v3/accounts/info/', get_account_info),
    # path('api/v3/accounts/dashboard/', get_account_info),
    # path('api/v3/accounts/edit/profile/', edit_profile_data),

    # Enable 2FA
    path('api/v1/new/message/', new_message),
    path('api/v3/get/attachement/<int:attachment>/', get_attachment)

] + router.urls
