"""
Custom renderers for API responses.

This module provides custom renderers that wrap all API responses
in a consistent envelope format.
"""

from collections import OrderedDict

from rest_framework.renderers import JSONRenderer


class CustomJSONRenderer(JSONRenderer):
    """
    Custom JSON renderer that wraps all responses in a consistent envelope.

    Response format:
    {
        "success": true/false,
        "data": {...} or [...],
        "errors": {...} or null,
        "meta": {...}
    }

    For paginated responses, the pagination metadata is already in the response
    from CustomPageNumberPagination, so we don't wrap those again.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render data into JSON with consistent envelope format.
        """
        response = renderer_context.get('response') if renderer_context else None

        # Don't wrap if data is already in envelope format (from pagination or custom views)
        if isinstance(data, dict) and 'success' in data:
            return super().render(data, accepted_media_type, renderer_context)

        # Handle error responses
        if response and not (200 <= response.status_code < 300):
            # Error responses are already formatted by custom_exception_handler
            if isinstance(data, dict) and 'errors' in data:
                return super().render(data, accepted_media_type, renderer_context)

            # If not already formatted, wrap it
            envelope = OrderedDict([('success', False), ('data', None), ('errors', data), ('meta', OrderedDict())])
            return super().render(envelope, accepted_media_type, renderer_context)

        # Wrap successful responses
        envelope = OrderedDict([('success', True), ('data', data), ('meta', OrderedDict())])

        return super().render(envelope, accepted_media_type, renderer_context)


class PlainJSONRenderer(JSONRenderer):
    """
    Plain JSON renderer without envelope wrapping.

    Use this for specific endpoints that need unwrapped responses.
    """

    pass
