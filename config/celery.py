"""
Celery configuration for Django project.

This module sets up Celery for the Django application with proper
configuration, task routing, and error handling.
"""

import os
from celery import Celery
from celery.signals import setup_logging
from django.conf import settings

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

# Create Celery app
app = Celery('config')

# Load configuration from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@setup_logging.connect
def config_loggers(*args, **kwargs):
    """Configure Celery logging to use Django logging configuration."""
    from logging.config import dictConfig
    from django.conf import settings
    dictConfig(settings.LOGGING)


# Task routing configuration
app.conf.task_routes = {
    'apps.users.tasks.*': {'queue': 'users'},
    'apps.core.tasks.*': {'queue': 'default'},
}

# Task retry configuration
app.conf.task_annotations = {
    '*': {
        'max_retries': 3,
        'default_retry_delay': 60,
        'autoretry_for': (Exception,),
        'retry_backoff': True,
        'retry_backoff_max': 600,
        'retry_jitter': True,
    }
}

# Task result expiration
app.conf.result_expires = 3600

# Task compression
app.conf.task_compression = 'gzip'
app.conf.result_compression = 'gzip'

# Worker configuration
app.conf.worker_send_task_events = True
app.conf.task_send_sent_event = True

# Prefetch settings for better distribution
app.conf.worker_prefetch_multiplier = 4

# Task priority support
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f'Request: {self.request!r}')
