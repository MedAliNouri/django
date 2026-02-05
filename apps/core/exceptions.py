"""
Custom exception handling for the API.

This module provides a custom exception handler that wraps all API responses
in a consistent envelope format with proper error handling.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework.exceptions import (
    APIException,
    ValidationError,
    PermissionDenied,
    NotFound,
    AuthenticationFailed,
)
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that wraps all errors in a consistent format.

    Response format:
    {
        "success": false,
        "data": null,
        "errors": {
            "code": "error_code",
            "message": "Human-readable error message",
            "details": {...}  # Optional detailed validation errors
        },
        "meta": {
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # Log the exception
    logger.error(
        f"API Exception: {exc}",
        exc_info=True,
        extra={
            'context': context,
            'request': context.get('request')
        }
    )

    # Handle Django validation errors
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(detail=exc.message_dict if hasattr(exc, 'message_dict') else str(exc))
        response = exception_handler(exc, context)

    # If response is None, it's an unhandled exception
    if response is None:
        return Response(
            {
                'success': False,
                'data': None,
                'errors': {
                    'code': 'internal_server_error',
                    'message': 'An unexpected error occurred. Please try again later.',
                    'details': str(exc) if hasattr(exc, '__str__') else None
                },
                'meta': {}
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Customize the response format
    custom_response = {
        'success': False,
        'data': None,
        'errors': format_error_response(exc, response),
        'meta': {}
    }

    response.data = custom_response
    return response


def format_error_response(exc, response):
    """
    Format error response based on exception type.
    """
    error_code = get_error_code(exc)
    error_message = get_error_message(exc)
    error_details = get_error_details(response.data)

    error_response = {
        'code': error_code,
        'message': error_message,
    }

    if error_details:
        error_response['details'] = error_details

    return error_response


def get_error_code(exc):
    """
    Get error code based on exception type.
    """
    error_codes = {
        ValidationError: 'validation_error',
        PermissionDenied: 'permission_denied',
        NotFound: 'not_found',
        Http404: 'not_found',
        AuthenticationFailed: 'authentication_failed',
    }

    for exc_type, code in error_codes.items():
        if isinstance(exc, exc_type):
            return code

    # Check for custom error code attribute
    if hasattr(exc, 'default_code'):
        return exc.default_code

    return 'error'


def get_error_message(exc):
    """
    Get human-readable error message.
    """
    if isinstance(exc, ValidationError):
        return 'Validation failed. Please check your input.'
    elif isinstance(exc, PermissionDenied):
        return 'You do not have permission to perform this action.'
    elif isinstance(exc, (NotFound, Http404)):
        return 'The requested resource was not found.'
    elif isinstance(exc, AuthenticationFailed):
        return 'Authentication credentials were not provided or are invalid.'

    # Use exception's detail if available
    if hasattr(exc, 'detail'):
        if isinstance(exc.detail, dict):
            # If detail is a dict, use a generic message
            return 'An error occurred processing your request.'
        return str(exc.detail)

    return str(exc)


def get_error_details(data):
    """
    Extract detailed error information from response data.
    """
    if isinstance(data, dict):
        # Remove 'detail' key as we use it for message
        details = {k: v for k, v in data.items() if k != 'detail'}
        return details if details else None
    elif isinstance(data, list):
        return data
    return None


class BusinessLogicError(APIException):
    """
    Custom exception for business logic errors.

    Use this for domain-specific errors that should be communicated
    to the client.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'A business logic error occurred.'
    default_code = 'business_logic_error'


class ResourceConflictError(APIException):
    """
    Exception for resource conflicts (e.g., duplicate resources).
    """
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'The resource conflicts with an existing resource.'
    default_code = 'resource_conflict'


class ServiceUnavailableError(APIException):
    """
    Exception for service unavailability.
    """
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'The service is temporarily unavailable.'
    default_code = 'service_unavailable'
