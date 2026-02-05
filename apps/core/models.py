"""
Core models module.

This module contains base model classes that other apps can inherit from.
"""

from django.db import models
from apps.common.behaviors import TimeStampedModel, UUIDModel, SoftDeleteModel


class BaseModel(UUIDModel, TimeStampedModel, SoftDeleteModel):
    """
    Base model combining UUID, timestamps, and soft delete functionality.

    All application models should inherit from this base model for
    consistent behavior across the application.
    """

    class Meta:
        abstract = True

    def __str__(self):
        """Default string representation."""
        return f"{self.__class__.__name__}({self.id})"

    def __repr__(self):
        """Developer-friendly representation."""
        return f"<{self.__class__.__name__} id={self.id}>"
