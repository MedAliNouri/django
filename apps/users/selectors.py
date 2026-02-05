"""
Selectors for User read operations.

This module contains all read/query logic for the User domain.
Selectors are pure functions that return data without side effects.
"""

from typing import Any

from django.core.cache import cache
from django.db.models import Q, QuerySet

from .models import User, UserProfile
from .repositories import UserProfileRepository, UserRepository


def get_user_by_id(user_id: str) -> User | None:
    """
    Get user by ID.

    Args:
        user_id: User UUID

    Returns:
        User instance or None
    """
    return UserRepository.get_by_id(user_id)


def get_user_by_email(email: str) -> User | None:
    """
    Get user by email.

    Args:
        email: User email address

    Returns:
        User instance or None
    """
    return UserRepository.get_by_email(email)


def user_exists(email: str) -> bool:
    """
    Check if user exists with given email.

    Args:
        email: Email address to check

    Returns:
        True if user exists, False otherwise
    """
    return UserRepository.exists_by_email(email)


def get_user_list(
    is_active: bool | None = None, is_verified: bool | None = None, search: str | None = None
) -> QuerySet:
    """
    Get list of users with optional filters.

    Args:
        is_active: Filter by active status
        is_verified: Filter by verified status
        search: Search query for email/name

    Returns:
        QuerySet of users
    """
    queryset = UserRepository.get_all()

    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)

    if is_verified is not None:
        queryset = queryset.filter(is_verified=is_verified)

    if search:
        queryset = queryset.filter(
            Q(email__icontains=search) | Q(first_name__icontains=search) | Q(last_name__icontains=search)
        )

    return queryset.select_related('profile').order_by('-created_at')


def get_user_with_profile(user_id: str) -> User | None:
    """
    Get user with profile prefetched.

    Args:
        user_id: User UUID

    Returns:
        User instance with profile or None
    """
    try:
        return User.objects.select_related('profile').get(id=user_id)
    except User.DoesNotExist:
        return None


def get_user_profile(user: User) -> UserProfile | None:
    """
    Get user profile.

    Args:
        user: User instance

    Returns:
        UserProfile instance or None
    """
    return UserProfileRepository.get_by_user(user)


def get_user_stats() -> dict[str, Any]:
    """
    Get user statistics.

    Returns:
        Dictionary with user statistics
    """
    cache_key = 'user_stats'
    stats = cache.get(cache_key)

    if stats is None:
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        verified_users = User.objects.filter(is_verified=True).count()
        staff_users = User.objects.filter(is_staff=True).count()

        stats = {
            'total': total_users,
            'active': active_users,
            'verified': verified_users,
            'staff': staff_users,
            'inactive': total_users - active_users,
            'unverified': total_users - verified_users,
        }

        cache.set(cache_key, stats, 300)  # Cache for 5 minutes

    return stats


def search_users(query: str, limit: int = 20) -> QuerySet:
    """
    Search users by email or name.

    Args:
        query: Search query
        limit: Maximum number of results

    Returns:
        QuerySet of matching users
    """
    return UserRepository.search(query)[:limit]


def get_recent_users(days: int = 7) -> QuerySet:
    """
    Get recently registered users.

    Args:
        days: Number of days to look back

    Returns:
        QuerySet of recent users
    """
    from datetime import timedelta

    from django.utils import timezone

    since = timezone.now() - timedelta(days=days)
    return User.objects.filter(created_at__gte=since, is_deleted=False).order_by('-created_at')


def is_email_available(email: str) -> bool:
    """
    Check if email is available for registration.

    Args:
        email: Email address to check

    Returns:
        True if email is available, False otherwise
    """
    return not UserRepository.exists_by_email(email)
