"""
Custom model managers for User models.

This module provides custom querysets and managers for advanced querying.
"""

from django.db import models
from django.utils import timezone
from datetime import timedelta


class UserQuerySet(models.QuerySet):
    """
    Custom queryset for User model with common query methods.
    """

    def active(self):
        """Return only active users."""
        return self.filter(is_active=True, is_deleted=False)

    def verified(self):
        """Return only verified users."""
        return self.filter(is_verified=True, is_deleted=False)

    def staff(self):
        """Return only staff users."""
        return self.filter(is_staff=True, is_deleted=False)

    def recent(self, days=7):
        """Return users created in the last N days."""
        since = timezone.now() - timedelta(days=days)
        return self.filter(created_at__gte=since)

    def by_email(self, email):
        """Get user by email (case-insensitive)."""
        return self.filter(email__iexact=email).first()

    def search(self, query):
        """
        Search users by email, first name, or last name.
        """
        return self.filter(
            models.Q(email__icontains=query) |
            models.Q(first_name__icontains=query) |
            models.Q(last_name__icontains=query)
        )

    def with_profile(self):
        """Select related profile to avoid N+1 queries."""
        return self.select_related('profile')
