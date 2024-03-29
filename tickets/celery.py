from celery import Celery

from tickets.settings import APP_NAME_CELERY, PORTREDIS
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tickets.settings')

app = Celery(APP_NAME_CELERY, broker=PORTREDIS)
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

