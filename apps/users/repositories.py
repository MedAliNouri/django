"""
Repository pattern for User data access.

This module abstracts database operations behind a clean interface.
All database queries should go through repositories.
"""

from django.db.models import QuerySet

from .models import User, UserProfile


class UserRepository:
    """
    Repository for User model data access.

    Provides a clean interface for all User database operations.
    """

    @staticmethod
    def get_by_id(user_id: str) -> User | None:
        """Get user by ID."""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_by_email(email: str) -> User | None:
        """Get user by email (case-insensitive)."""
        try:
            return User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return None

    @staticmethod
    def exists_by_email(email: str) -> bool:
        """Check if user exists with given email."""
        return User.objects.filter(email__iexact=email).exists()

    @staticmethod
    def create(email: str, password: str, **kwargs) -> User:
        """Create a new user."""
        return User.objects.create_user(email=email, password=password, **kwargs)

    @staticmethod
    def update(user: User, **kwargs) -> User:
        """Update user fields."""
        for key, value in kwargs.items():
            setattr(user, key, value)
        user.save(update_fields=kwargs.keys())
        return user

    @staticmethod
    def delete(user: User, hard: bool = False) -> None:
        """Delete user (soft delete by default)."""
        user.delete(hard=hard)

    @staticmethod
    def get_all() -> QuerySet:
        """Get all active users."""
        return User.objects.filter(is_deleted=False)

    @staticmethod
    def get_active_users() -> QuerySet:
        """Get all active, non-deleted users."""
        return User.objects.filter(is_active=True, is_deleted=False)

    @staticmethod
    def get_verified_users() -> QuerySet:
        """Get all verified users."""
        return User.objects.filter(is_verified=True, is_deleted=False)

    @staticmethod
    def search(query: str) -> QuerySet:
        """Search users by email or name."""
        return (
            User.objects.filter(email__icontains=query)
            | User.objects.filter(first_name__icontains=query)
            | User.objects.filter(last_name__icontains=query)
        )

    @staticmethod
    def bulk_create(users: list[dict]) -> list[User]:
        """Bulk create users."""
        user_objects = [User(**user_data) for user_data in users]
        return User.objects.bulk_create(user_objects)


class UserProfileRepository:
    """
    Repository for UserProfile model data access.
    """

    @staticmethod
    def get_by_user(user: User) -> UserProfile | None:
        """Get profile by user."""
        try:
            return UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            return None

    @staticmethod
    def create(user: User, **kwargs) -> UserProfile:
        """Create user profile."""
        return UserProfile.objects.create(user=user, **kwargs)

    @staticmethod
    def update(profile: UserProfile, **kwargs) -> UserProfile:
        """Update profile fields."""
        for key, value in kwargs.items():
            setattr(profile, key, value)
        profile.save(update_fields=kwargs.keys())
        return profile

    @staticmethod
    def get_or_create(user: User, **kwargs) -> tuple:
        """Get or create user profile."""
        return UserProfile.objects.get_or_create(user=user, defaults=kwargs)
