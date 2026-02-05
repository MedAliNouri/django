"""
Base views and viewsets for the API.

This module provides base view classes with common functionality
and best practices.
"""

from django.core.cache import cache
from django.db import connection
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class BaseModelViewSet(viewsets.ModelViewSet):
    """
    Base viewset with common functionality.

    Provides:
    - Automatic queryset filtering for soft-deleted objects
    - Per-action serializer classes
    - Per-action permission classes
    """

    # Override these in subclasses
    serializer_classes = {}
    permission_classes_by_action = {}

    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the action.

        Example:
            serializer_classes = {
                'create': CreateUserSerializer,
                'update': UpdateUserSerializer,
                'list': ListUserSerializer,
            }
        """
        return self.serializer_classes.get(self.action, super().get_serializer_class())

    def get_permissions(self):
        """
        Return the appropriate permissions based on the action.

        Example:
            permission_classes_by_action = {
                'create': [AllowAny],
                'destroy': [IsAdmin],
            }
        """
        try:
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            return super().get_permissions()

    def get_queryset(self):
        """
        Filter out soft-deleted objects by default.

        Override this method if you need custom queryset logic.
        """
        queryset = super().get_queryset()

        # Filter soft-deleted objects if model has is_deleted field
        if hasattr(queryset.model, 'is_deleted'):
            queryset = queryset.filter(is_deleted=False)

        return queryset

    def perform_destroy(self, instance):
        """
        Soft delete by default if model supports it.

        For hard delete, override this method.
        """
        if hasattr(instance, 'is_deleted'):
            instance.delete()  # Uses soft delete from SoftDeleteModel
        else:
            instance.delete(hard=True)


class HealthCheckView(APIView):
    """
    Health check endpoint for monitoring and load balancers.

    Returns the health status of the application and its dependencies.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """
        Check health of database, cache, and application.
        """
        health_status = {'status': 'healthy', 'checks': {}}
        overall_healthy = True

        # Check database
        try:
            connection.ensure_connection()
            health_status['checks']['database'] = {'status': 'healthy', 'message': 'Database connection successful'}
        except Exception as e:
            overall_healthy = False
            health_status['checks']['database'] = {'status': 'unhealthy', 'message': str(e)}

        # Check Redis/Cache
        try:
            cache.set('health_check', 'ok', 10)
            cache_value = cache.get('health_check')
            if cache_value == 'ok':
                health_status['checks']['cache'] = {'status': 'healthy', 'message': 'Cache connection successful'}
            else:
                raise Exception('Cache read/write failed')
        except Exception as e:
            overall_healthy = False
            health_status['checks']['cache'] = {'status': 'unhealthy', 'message': str(e)}

        # Set overall status
        health_status['status'] = 'healthy' if overall_healthy else 'unhealthy'

        return Response(
            health_status, status=status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        )
