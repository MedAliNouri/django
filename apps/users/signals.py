"""
Signal handlers for User models.

This module contains signal handlers for User-related events.
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.cache import cache
import logging

from .models import User, UserProfile

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create user profile when user is created.
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)
        logger.info(f"Profile created for user: {instance.email}")


@receiver(post_save, sender=User)
def invalidate_user_cache(sender, instance, **kwargs):
    """
    Invalidate user-related cache on save.
    """
    cache.delete('user_stats')
    cache.delete(f'user_{instance.id}')


@receiver(pre_delete, sender=User)
def log_user_deletion(sender, instance, **kwargs):
    """
    Log user deletion for audit purposes.
    """
    logger.warning(
        f"User deleted: {instance.email}",
        extra={
            'user_id': str(instance.id),
            'email': instance.email,
            'is_hard_delete': not hasattr(instance, 'is_deleted') or instance.is_deleted
        }
    )
