import os
from celery import Celery
from celery import shared_task
from kombu import Queue

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
# Skip Django system checks when starting Celery worker.
# This avoids worker boot failure on URL/model check issues unrelated to task execution.
os.environ.setdefault('CELERY_SKIP_CHECKS', 'true')

app = Celery('backend')

# Load config from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


app.conf.beat_schedule = {
    # Add periodic tasks here if needed
}

app.conf.task_default_queue = 'default'
app.conf.task_queues = (
    Queue('default'),
    Queue('ml_train'),
)
app.conf.task_routes = {
    'playground.tasks.run_training_task': {'queue': 'ml_train'},
}

# Task time limits
app.conf.task_time_limit = 300  # 5 minutes
app.conf.task_soft_time_limit = 240

