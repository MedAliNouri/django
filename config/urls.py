"""
URL Configuration for the Django project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from apps.core.views import HealthCheckView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Health check
    path('health/', HealthCheckView.as_view(), name='health-check'),

    # API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API versioned endpoints
    path('api/v1/', include(('apps.users.api.v1.urls', 'v1'), namespace='v1')),
    path('api/v2/', include(('apps.users.api.v2.urls', 'v2'), namespace='v2')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Debug toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# Customize admin site
admin.site.site_header = 'Django REST API Administration'
admin.site.site_title = 'Django REST API Admin'
admin.site.index_title = 'Welcome to Django REST API Administration'
