"""
Services for User write operations.

This module contains all write/business logic for the User domain.
Services handle complex operations, validations, and orchestrate
between repositories and other services.
"""

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import BusinessLogicError, ResourceConflictError

from .models import User, UserProfile
from .repositories import UserProfileRepository, UserRepository
from .selectors import user_exists


class UserService:
    """
    Service for User domain write operations.

    All business logic and write operations go through this service.
    """

    @staticmethod
    @transaction.atomic
    def create_user(email: str, password: str, first_name: str = '', last_name: str = '', **extra_fields) -> User:
        """
        Create a new user with profile.

        Args:
            email: User email
            password: User password
            first_name: User first name
            last_name: User last name
            **extra_fields: Additional user fields

        Returns:
            Created User instance

        Raises:
            ResourceConflictError: If user with email already exists
        """
        # Validate email availability
        if user_exists(email):
            raise ResourceConflictError(f'User with email {email} already exists')

        # Create user
        user = UserRepository.create(
            email=email, password=password, first_name=first_name, last_name=last_name, **extra_fields
        )

        # Create profile
        UserProfileRepository.create(user=user)

        # Invalidate user stats cache
        cache.delete('user_stats')

        return user

    @staticmethod
    @transaction.atomic
    def update_user(user: User, **update_fields) -> User:
        """
        Update user fields.

        Args:
            user: User instance to update
            **update_fields: Fields to update

        Returns:
            Updated User instance
        """
        # Validate email uniqueness if being changed
        if 'email' in update_fields:
            new_email = update_fields['email']
            if new_email != user.email and user_exists(new_email):
                raise ResourceConflictError(f'Email {new_email} is already taken')

        # Update user
        updated_user = UserRepository.update(user, **update_fields)

        # Invalidate cache
        cache.delete('user_stats')

        return updated_user

    @staticmethod
    @transaction.atomic
    def update_user_profile(user: User, **profile_fields) -> UserProfile:
        """
        Update user profile.

        Args:
            user: User instance
            **profile_fields: Profile fields to update

        Returns:
            Updated UserProfile instance
        """
        profile, created = UserProfileRepository.get_or_create(user=user)

        if not created:
            profile = UserProfileRepository.update(profile, **profile_fields)
        else:
            # If just created, update with provided fields
            for key, value in profile_fields.items():
                setattr(profile, key, value)
            profile.save()

        return profile

    @staticmethod
    @transaction.atomic
    def delete_user(user: User, hard: bool = False) -> None:
        """
        Delete user (soft delete by default).

        Args:
            user: User instance to delete
            hard: If True, permanently delete user

        Raises:
            BusinessLogicError: If user is superuser and trying to delete
        """
        if user.is_superuser and not hard:
            raise BusinessLogicError('Cannot soft delete superuser')

        UserRepository.delete(user, hard=hard)

        # Invalidate cache
        cache.delete('user_stats')

    @staticmethod
    def change_password(user: User, old_password: str, new_password: str) -> User:
        """
        Change user password.

        Args:
            user: User instance
            old_password: Current password
            new_password: New password

        Returns:
            Updated User instance

        Raises:
            BusinessLogicError: If old password is incorrect
        """
        if not user.check_password(old_password):
            raise BusinessLogicError('Current password is incorrect')

        user.set_password(new_password)
        user.save(update_fields=['password'])

        return user

    @staticmethod
    def activate_user(user: User) -> User:
        """
        Activate user account.

        Args:
            user: User instance to activate

        Returns:
            Updated User instance
        """
        return UserRepository.update(user, is_active=True)

    @staticmethod
    def deactivate_user(user: User) -> User:
        """
        Deactivate user account.

        Args:
            user: User instance to deactivate

        Returns:
            Updated User instance
        """
        return UserRepository.update(user, is_active=False)

    @staticmethod
    def verify_email(user: User) -> User:
        """
        Mark user email as verified.

        Args:
            user: User instance

        Returns:
            Updated User instance
        """
        return UserRepository.update(user, is_verified=True, email_verified_at=timezone.now())

    @staticmethod
    def update_last_login(user: User, ip_address: str) -> User:
        """
        Update user's last login information.

        Args:
            user: User instance
            ip_address: IP address of login

        Returns:
            Updated User instance
        """
        return UserRepository.update(user, last_login=timezone.now(), last_login_ip=ip_address)


class UserBulkService:
    """
    Service for bulk user operations.
    """

    @staticmethod
    @transaction.atomic
    def bulk_create_users(users_data: list) -> list:
        """
        Bulk create users.

        Args:
            users_data: List of user data dictionaries

        Returns:
            List of created User instances
        """
        # Validate all emails are unique
        emails = [user_data['email'] for user_data in users_data]
        if len(emails) != len(set(emails)):
            raise BusinessLogicError('Duplicate emails in bulk create')

        # Check if any email already exists
        for email in emails:
            if user_exists(email):
                raise ResourceConflictError(f'Email {email} already exists')

        # Create users
        users = UserRepository.bulk_create(users_data)

        # Create profiles for all users
        profiles = [UserProfile(user=user) for user in users]
        UserProfile.objects.bulk_create(profiles)

        # Invalidate cache
        cache.delete('user_stats')

        return users

    @staticmethod
    @transaction.atomic
    def bulk_delete_users(user_ids: list, hard: bool = False) -> int:
        """
        Bulk delete users.

        Args:
            user_ids: List of user IDs to delete
            hard: If True, permanently delete users

        Returns:
            Number of users deleted
        """
        users = User.objects.filter(id__in=user_ids)

        if hard:
            count = users.count()
            users.delete()
        else:
            count = users.update(is_deleted=True, deleted_at=timezone.now())

        # Invalidate cache
        cache.delete('user_stats')

        return count
