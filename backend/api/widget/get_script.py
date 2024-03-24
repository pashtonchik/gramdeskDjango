import datetime

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.response import Response
import json
from rest_framework_simplejwt.tokens import RefreshToken
from backend.models import User, JWTToken, TelegramBot, Platform, Ticket
from django.contrib.auth.hashers import make_password
from django.db import transaction
import logging
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework.decorators import api_view
import pyotp
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import HttpResponse
from backend.serializers import TicketSerializer, TicketMessageSerializer


@api_view(["GET"])
@transaction.atomic()
def widget_client_auth(request):
    return HttpResponse("parent.Response_OK()", content_type="application/x-javascript")
