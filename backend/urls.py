from rest_framework import routers
from django.urls import path

from backend.api.client_info.block_client import block_client
from backend.api.client_info.client_info import get_client
from backend.api.client_info.unblock_client import unblock_client
from backend.api.client_info.update_client import update_client_info
from backend.api.files.get_file import get_attachment
from backend.api.info.get import get_info
from backend.api.message_from_telegram.message_from_user import telegram
from backend.api.platform_management.update_platform import update_platform_info
from backend.api.profiat_accounts.auth import profiat_auth_client
from backend.api.profiat_accounts.close_access import close_access
from backend.api.profiat_accounts.refresh import refresh as refresh_profiat
from backend.api.support_accounts.add_support import add_new_support
from backend.api.support_accounts.delete_support import delete_support
from backend.api.support_accounts.edit_password import edit_password
from backend.api.support_accounts.edit_profile import edit_profile_data
from backend.api.support_accounts.refresh import refresh as refresh_support
from backend.api.support_accounts.auth import auth, abc123
from backend.api.support_accounts.auth_verify import verify_token
from backend.api.support_accounts.restore import restore
from backend.api.support_accounts.signup import *
from backend.api.support_accounts.signup_new_code import registrate_req_new_code
from backend.api.telegram_managment.add_telegram_bot import create_telegram_bot
from backend.api.telegram_managment.delete_telegram_bot import delete_telegram_bot
from backend.api.telegram_managment.edit_telegram_bot import edit_telegram_bot
from backend.api.telegram_managment.get_telegram_bot import get_telegram_bot
from backend.api.vk.events import vk_event
from backend.api.vk_managment.delete_vk_bot import delete_vk_bot
from backend.api.vk_managment.edit_vk_bot import edit_vk_bot
from backend.api.widget.get_script import widget_script
from backend.api.widget.new_client import widget_client_auth
from backend.permissions import ProfiatIntegration

router = routers.DefaultRouter()

urlpatterns = [
    # Profiat
    path('api/v2/client/auth/', profiat_auth_client),
    path('api/v2/client/auth/refresh/', refresh_profiat),
    path('api/v2/client/auth/close/access/', close_access),
    path('api/abc/', abc123),

    path('api/v3/support/get/info/', get_info),

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
    path('api/v3/support/update/profile/', edit_profile_data),
    path('api/v3/support/update/password/', edit_password),

    path('api/v3/support/restore/', restore),

    #Supports Managment
    path('api/v3/support/delete/user/', delete_support),
    path('api/v3/support/create/user/', add_new_support),

    # Clients Management
    path('api/v3/support/update/client/', update_client_info),
    path('api/v3/support/block/client/', block_client),
    path('api/v3/support/unblock/client/', unblock_client),
    path('api/v3/support/get/client/', get_client),

    # Platform Management
    path('api/v3/support/update/platform/', update_platform_info),


    # Telegram Bots Managment
    path('api/v3/support/edit/telegram/bot/', edit_telegram_bot),
    path('api/v3/support/get/telegram/bot/', get_telegram_bot),
    path('api/v3/support/delete/telegram/bot/', delete_telegram_bot),
    path('api/v3/support/create/telegram/bot/', create_telegram_bot),

    # Widget Client
    path('api/v2/clients/registrate/', widget_client_auth),
    path('api/clientScript.js/<str:platform>/', widget_script),


    #VK
    path('vk/<str:platform_id>/', vk_event),


    #Vk Managment
    path('api/v3/support/edit/vk/bot/', edit_vk_bot),
    path('api/v3/support/delete/vk/bot/', delete_vk_bot),

] + router.urls
