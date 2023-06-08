"""Celery config for app."""

from datetime import timedelta
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
app = Celery('mysite')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'check-credits-days': {
        'task': 'bank_app.tasks.check_credits',
        'schedule': timedelta(days=1),
    },
    'check-payments-minute': {
        'task': 'bank_app.tasks.check_payments',
        'schedule': timedelta(days=1),
    },
    'check-investments-days': {
        'task': 'bank_app.tasks.check_investments',
        'schedule': timedelta(minutes=1),
    },
}
