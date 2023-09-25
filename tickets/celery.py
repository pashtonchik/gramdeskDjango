from celery import Celery

from tickets.background.heart_beat import heart_beat_connector
from tickets.settings import APP_NAME_CELERY
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tickets.settings')

app = Celery(APP_NAME_CELERY)
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(15.0, update_items_fee.s())


@app.task
def update_items_fee():
    heart_beat_connector()

