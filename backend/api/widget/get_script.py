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
def widget_script(request):

    script = """
        window.onload = function() {
            var iframe = document.createElement('iframe');
            iframe.src = 'http://localhost:3001/123';
            iframe.id = 'fixed-iframe';

            iframe.style.position = 'fixed';
            iframe.style.bottom = '10px';
            iframe.style.right = '10px';
            iframe.style.border = 'none';
            iframe.style.borderRadius = '10px';
            iframe.style.height = '60px';
            // iframe.style.width = '40px';

            document.body.appendChild(iframe);
        };

        // Функция для обработки сообщений от источника iframe
        function handleMessage(event) {
            console.log('Получено сообщение:', event.data);
            if (event.data && event.data.type === 'resize') {
            // Изменение высоты iframe
            document.getElementById('fixed-iframe').style.height = event.data.height + 'px';
        }
        }

        // Добавление обработчика события message
        window.addEventListener('message', handleMessage);    
    
    """

    return HttpResponse("parent.Response_OK()", content_type="application/x-javascript")
