import os
from celery import Celery
from celery.signals import task_failure
from .settings import INSTALLED_APPS

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault(key="DJANGO_SETTINGS_MODULE", value="orders.settings")

celery_app = Celery(
    main="orders",
)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
celery_app.config_from_object(obj="django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
celery_app.autodiscover_tasks(lambda: INSTALLED_APPS)

if bool(os.environ.get('CELERY_WORKER_RUNNING', False)):
    from django.conf import settings
    import rollbar
    rollbar.init(**settings.ROLLBAR)

    def celery_base_data_hook(request, data):
        data['framework'] = 'celery'

    rollbar.BASE_DATA_HOOK = celery_base_data_hook

    @task_failure.connect
    def handle_task_failure(**kw):
        rollbar.report_exc_info(extra_data=kw)


@celery_app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
