from celery import Celery
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid

from django.db.models import Subquery, OuterRef

from tickets.settings import APP_NAME_CELERY
from datetime import datetime
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tickets.settings')

app = Celery(APP_NAME_CELERY)
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
