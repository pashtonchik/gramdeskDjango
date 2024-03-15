from celery import Celery

from tickets.background.heart_beat import heart_beat_connector
from tickets.settings import APP_NAME_CELERY
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tickets.settings')

app = Celery(APP_NAME_CELERY)
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

