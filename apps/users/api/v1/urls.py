"""
API v1 URLs for User endpoints.

This module defines URL patterns for the User API v1.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views import UserViewSet
from .keycloak_views import (
    KeycloakConfigView,
    KeycloakLoginView,
    KeycloakLogoutView,
    KeycloakRefreshView,
    KeycloakUserInfoView,
)
from .debug_views import KeucloakTokenDebugView

# Create router and register viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # JWT Authentication (Django)
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # Keycloak Authentication
    path('auth/keycloak/login/', KeycloakLoginView.as_view(), name='keycloak_login'),
    path('auth/keycloak/refresh/', KeycloakRefreshView.as_view(), name='keycloak_refresh'),
    path('auth/keycloak/logout/', KeycloakLogoutView.as_view(), name='keycloak_logout'),
    path('auth/keycloak/userinfo/', KeycloakUserInfoView.as_view(), name='keycloak_userinfo'),
    path('auth/keycloak/config/', KeycloakConfigView.as_view(), name='keycloak_config'),
    path('auth/keycloak/debug/', KeucloakTokenDebugView.as_view(), name='keycloak_debug'),
    # User endpoints
    path('', include(router.urls)),
]
