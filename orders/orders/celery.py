import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault(key='DJANGO_SETTINGS_MODULE', value='orders.settings')

app = Celery(main='orders', broker="amqp://guest@rabbitmq//")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object(obj='django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    "periodic_add_numbers": {
        "task": "orders.tasks.add_numbers", "schedule": crontab(minute="*/1"),
    },
}
# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
