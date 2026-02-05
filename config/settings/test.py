"""
Test settings.

This file contains settings specific to running tests.
Optimized for speed and isolation.
"""

from .base import *  # noqa

# Use in-memory SQLite for faster tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Use simple password hasher for faster tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Use dummy cache backend for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}


# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# Email backend for tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Disable throttling in tests
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []

# Logging - Minimal logging in tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}

# Debug mode off for tests
DEBUG = False

# Allowed hosts
ALLOWED_HOSTS = ['*']

# Static files
STATIC_ROOT = BASE_DIR / 'test_staticfiles'
MEDIA_ROOT = BASE_DIR / 'test_mediafiles'

# Disable whitenoise for tests
MIDDLEWARE.remove('whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
