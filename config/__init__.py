"""
Django configuration package.

This package contains all Django configuration including settings, URLs, and WSGI/ASGI apps.
"""

# This will make sure the Celery app is always imported when Django starts
from .celery import app as celery_app

__all__ = ('celery_app',)
