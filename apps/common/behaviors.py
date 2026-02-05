"""
Model behaviors (mixins) for common functionality.

These mixins provide reusable model behaviors that can be added to any model.
"""

import uuid

from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    """
    Abstract base model with timestamp fields.

    Provides created_at and updated_at fields that are automatically
    managed by Django.
    """

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']


class UUIDModel(models.Model):
    """
    Abstract base model with UUID primary key.

    Uses UUID4 for primary keys instead of auto-incrementing integers
    for better security and distributed systems support.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Abstract base model with soft delete functionality.

    Provides is_deleted and deleted_at fields for soft deletion.
    Includes a custom manager to exclude deleted objects by default.
    """

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, hard=False):
        """
        Soft delete the object by default.
        Set hard=True for permanent deletion.
        """
        if hard:
            return super().delete(using=using, keep_parents=keep_parents)

        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        """Restore a soft-deleted object."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])


class SluggedModel(models.Model):
    """
    Abstract base model with slug field.

    Automatically generates a slug from a specified field.
    """

    slug = models.SlugField(max_length=255, unique=True, db_index=True)

    class Meta:
        abstract = True

    def generate_slug(self, source_field='name'):
        """Generate a unique slug from the source field."""
        base_slug = slugify(getattr(self, source_field, ''))
        slug = base_slug
        counter = 1

        while self.__class__.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f'{base_slug}-{counter}'
            counter += 1

        self.slug = slug


class PublishableModel(models.Model):
    """
    Abstract base model for publishable content.

    Provides published status and published_at timestamp.
    """

    class PublishStatus(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'

    status = models.CharField(max_length=20, choices=PublishStatus.choices, default=PublishStatus.DRAFT, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def publish(self):
        """Publish the content."""
        self.status = self.PublishStatus.PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=['status', 'published_at'])

    def unpublish(self):
        """Unpublish the content."""
        self.status = self.PublishStatus.DRAFT
        self.published_at = None
        self.save(update_fields=['status', 'published_at'])

    def archive(self):
        """Archive the content."""
        self.status = self.PublishStatus.ARCHIVED
        self.save(update_fields=['status'])


class AuthorModel(models.Model):
    """
    Abstract base model that tracks who created/modified the object.
    """

    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='%(class)s_created'
    )
    updated_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='%(class)s_updated'
    )

    class Meta:
        abstract = True
