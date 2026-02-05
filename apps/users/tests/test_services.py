"""
Tests for User services.
"""

import pytest

from apps.core.exceptions import BusinessLogicError, ResourceConflictError
from apps.users.models import User
from apps.users.services import UserService


@pytest.mark.django_db
class TestUserService:
    """Test UserService."""

    def test_create_user(self, user_data):
        """Test creating a user through service."""
        user = UserService.create_user(**user_data)

        assert user.email == user_data['email']
        assert user.check_password(user_data['password'])
        assert hasattr(user, 'profile')

    def test_create_user_duplicate_email(self, user, user_data):
        """Test creating user with duplicate email raises error."""
        with pytest.raises(ResourceConflictError):
            UserService.create_user(**user_data)

    def test_update_user(self, user):
        """Test updating user."""
        updated = UserService.update_user(user, first_name='Updated', last_name='Name')

        assert updated.first_name == 'Updated'
        assert updated.last_name == 'Name'

    def test_update_user_email_conflict(self, user, active_user):
        """Test updating to existing email raises error."""
        with pytest.raises(ResourceConflictError):
            UserService.update_user(user, email=active_user.email)

    def test_change_password(self, user):
        """Test changing password."""
        old_password = 'TestPass123!'
        new_password = 'NewPass456!'

        UserService.change_password(user, old_password, new_password)
        user.refresh_from_db()

        assert user.check_password(new_password)

    def test_change_password_wrong_old_password(self, user):
        """Test changing password with wrong old password."""
        with pytest.raises(BusinessLogicError):
            UserService.change_password(user, 'WrongPass', 'NewPass456!')

    def test_activate_user(self, user):
        """Test activating user."""
        user.is_active = False
        user.save()

        activated = UserService.activate_user(user)
        assert activated.is_active is True

    def test_deactivate_user(self, user):
        """Test deactivating user."""
        deactivated = UserService.deactivate_user(user)
        assert deactivated.is_active is False

    def test_verify_email(self, user):
        """Test verifying email."""
        verified = UserService.verify_email(user)

        assert verified.is_verified is True
        assert verified.email_verified_at is not None

    def test_delete_user(self, user):
        """Test soft deleting user."""
        UserService.delete_user(user)

        assert user.is_deleted is True
        assert User.objects.filter(id=user.id).count() == 0

    def test_cannot_soft_delete_superuser(self, superuser):
        """Test that superuser cannot be soft deleted."""
        with pytest.raises(BusinessLogicError):
            UserService.delete_user(superuser, hard=False)
