"""
Production settings.

This file contains settings specific to the production environment.
Security is paramount here.
"""

from .base import *  # noqa

# Ensure debug is False in production
DEBUG = False

# Strict allowed hosts
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

if not ALLOWED_HOSTS:
    raise ValueError('ALLOWED_HOSTS must be set in production')

# Database SSL requirement for production
if config('DB_SSL_REQUIRE', default=True, cast=bool):
    DATABASES['default']['OPTIONS']['sslmode'] = 'require'

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SAMESITE = 'Strict'

# Additional security headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CORS - Strict origins in production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', cast=Csv())

# Session security
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_NAME = 'sessionid'

# CSRF token security
CSRF_COOKIE_AGE = 31449600  # 1 year
CSRF_USE_SESSIONS = False

# Logging - Add file handler in production
LOGGING['handlers']['file']['level'] = 'WARNING'
LOGGING['root']['handlers'] = ['console', 'file']

# Sentry integration for error tracking
SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment='production',
    )

# Cache - Production settings with longer timeout
CACHES['default']['TIMEOUT'] = 600
CACHES['default']['OPTIONS']['CONNECTION_POOL_CLASS_KWARGS']['max_connections'] = 100

# Celery - Production settings
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 500

# Email - Production SMTP settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')

# Admin notifications
ADMINS = [
    (config('ADMIN_NAME', default='Admin'), config('ADMIN_EMAIL', default='admin@example.com')),
]
MANAGERS = ADMINS

# Static files - Use whitenoise with compression
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Ensure secret key is set and strong
if SECRET_KEY == 'django-insecure-change-this-in-production':
    raise ValueError('SECRET_KEY must be set to a strong value in production')

# Database connection pooling
DATABASES['default']['CONN_MAX_AGE'] = 600

# Disable browsable API in production
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'apps.core.renderers.CustomJSONRenderer',
]
