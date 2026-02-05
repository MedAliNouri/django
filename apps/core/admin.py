"""
Core admin configuration.

This module provides base admin classes with common functionality.
"""

from django.contrib import admin


class BaseModelAdmin(admin.ModelAdmin):
    """
    Base admin class with common configuration.
    """

    readonly_fields = ('id', 'created_at', 'updated_at')
    list_per_page = 25
    show_full_result_count = True
    date_hierarchy = 'created_at'

    def get_list_display(self, request):
        """
        Add timestamp fields to list display if not already present.
        """
        list_display = list(super().get_list_display(request))

        # Add timestamps if model has them
        if hasattr(self.model, 'created_at') and 'created_at' not in list_display:
            list_display.append('created_at')
        if hasattr(self.model, 'updated_at') and 'updated_at' not in list_display:
            list_display.append('updated_at')

        return list_display

    def get_readonly_fields(self, request, obj=None):
        """
        Make all fields readonly when editing if specified.
        """
        readonly_fields = list(super().get_readonly_fields(request, obj))

        # Add soft delete fields if model has them
        if hasattr(self.model, 'is_deleted'):
            readonly_fields.extend(['is_deleted', 'deleted_at'])

        return readonly_fields
