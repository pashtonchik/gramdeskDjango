from rest_framework import routers
from django.urls import path

from backend.api.message_from_telegram.message_from_user import new_message

router = routers.DefaultRouter()

urlpatterns = [
    # path('api/v3/accounts/auth/verify/', verify_token),
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
    path('api/v1/new/message/', new_message)

] + router.urls
