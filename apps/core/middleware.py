"""
Custom middleware for the application.

This module provides middleware for correlation IDs, request logging,
and other cross-cutting concerns.
"""

import logging
import time
import uuid

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class CorrelationIDMiddleware(MiddlewareMixin):
    """
    Middleware to inject correlation IDs into requests and responses.

    A correlation ID is a unique identifier for each request that can be
    used to trace the request through the entire system (logs, Celery tasks, etc.).
    """

    CORRELATION_ID_HEADER = 'X-Correlation-ID'

    def process_request(self, request):
        """
        Add correlation ID to request.

        If the client provides a correlation ID in the header, use it.
        Otherwise, generate a new one.
        """
        correlation_id = request.META.get(f'HTTP_{self.CORRELATION_ID_HEADER.upper().replace("-", "_")}')

        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        request.correlation_id = correlation_id

    def process_response(self, request, response):
        """
        Add correlation ID to response headers.
        """
        if hasattr(request, 'correlation_id'):
            response[self.CORRELATION_ID_HEADER] = request.correlation_id

        return response


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all API requests and responses.

    Logs include request method, path, user, response status, and duration.
    """

    def process_request(self, request):
        """
        Log incoming request and record start time.
        """
        request._request_start_time = time.time()

        logger.info(
            f'Request started: {request.method} {request.path}',
            extra={
                'method': request.method,
                'path': request.path,
                'query_params': dict(request.GET),
                'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
                'correlation_id': getattr(request, 'correlation_id', None),
                'ip_address': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            },
        )

    def process_response(self, request, response):
        """
        Log response with timing information.
        """
        if hasattr(request, '_request_start_time'):
            duration = time.time() - request._request_start_time

            logger.info(
                f'Request completed: {request.method} {request.path} - {response.status_code}',
                extra={
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration_ms': round(duration * 1000, 2),
                    'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
                    'correlation_id': getattr(request, 'correlation_id', None),
                    'ip_address': self.get_client_ip(request),
                },
            )

        return response

    @staticmethod
    def get_client_ip(request):
        """
        Get client IP address from request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RequestIDMiddleware(MiddlewareMixin):
    """
    Alternative middleware for request IDs.

    Similar to CorrelationIDMiddleware but uses X-Request-ID header.
    """

    REQUEST_ID_HEADER = 'X-Request-ID'

    def process_request(self, request):
        """Add request ID to request."""
        request_id = request.META.get(f'HTTP_{self.REQUEST_ID_HEADER.upper().replace("-", "_")}')

        if not request_id:
            request_id = str(uuid.uuid4())

        request.request_id = request_id

    def process_response(self, request, response):
        """Add request ID to response headers."""
        if hasattr(request, 'request_id'):
            response[self.REQUEST_ID_HEADER] = request.request_id

        return response
