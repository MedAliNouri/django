"""
Custom pagination classes for the API.

This module provides pagination classes with consistent metadata
in API responses.
"""

from collections import OrderedDict

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPageNumberPagination(PageNumberPagination):
    """
    Custom pagination with consistent metadata structure.

    Returns pagination metadata in a 'meta' key for consistency
    with the envelope response format.
    """

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'

    def get_paginated_response(self, data):
        """
        Return paginated response with metadata.

        Response format:
        {
            "success": true,
            "data": [...],
            "meta": {
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total_count": 100,
                    "total_pages": 5,
                    "has_next": true,
                    "has_previous": false,
                    "next": "http://...",
                    "previous": null
                }
            }
        }
        """
        return Response(
            OrderedDict(
                [
                    ('success', True),
                    ('data', data),
                    (
                        'meta',
                        OrderedDict(
                            [
                                (
                                    'pagination',
                                    OrderedDict(
                                        [
                                            ('page', self.page.number),
                                            ('page_size', self.get_page_size(self.request)),
                                            ('total_count', self.page.paginator.count),
                                            ('total_pages', self.page.paginator.num_pages),
                                            ('has_next', self.page.has_next()),
                                            ('has_previous', self.page.has_previous()),
                                            ('next', self.get_next_link()),
                                            ('previous', self.get_previous_link()),
                                        ]
                                    ),
                                )
                            ]
                        ),
                    ),
                ]
            )
        )


class SmallPageNumberPagination(CustomPageNumberPagination):
    """
    Smaller page size for lists that typically have fewer items.
    """

    page_size = 10
    max_page_size = 50


class LargePageNumberPagination(CustomPageNumberPagination):
    """
    Larger page size for bulk data retrieval.
    """

    page_size = 50
    max_page_size = 200
