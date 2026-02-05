"""
Tests for User models.
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Test User model."""

    def test_create_user(self, user_data):
        """Test creating a regular user."""
        user = User.objects.create_user(**user_data)

        assert user.email == user_data['email']
        assert user.check_password(user_data['password'])
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='AdminPass123!',
            first_name='Admin',
            last_name='User',
        )

        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.is_active is True

    def test_user_str(self, user):
        """Test user string representation."""
        assert str(user) == user.email

    def test_get_full_name(self, user):
        """Test get_full_name method."""
        full_name = user.get_full_name()
        assert full_name == f"{user.first_name} {user.last_name}"

    def test_get_short_name(self, user):
        """Test get_short_name method."""
        assert user.get_short_name() == user.first_name

    def test_email_required(self):
        """Test that email is required."""
        with pytest.raises(ValueError):
            User.objects.create_user(email='', password='password')

    def test_soft_delete(self, user):
        """Test soft delete functionality."""
        user.delete()

        assert user.is_deleted is True
        assert user.deleted_at is not None
        assert User.objects.filter(id=user.id).count() == 0
        assert User.objects.with_deleted().filter(id=user.id).count() == 1

    def test_hard_delete(self, user):
        """Test hard delete functionality."""
        user_id = user.id
        user.delete(hard=True)

        assert User.objects.with_deleted().filter(id=user_id).count() == 0


@pytest.mark.django_db
class TestUserProfile:
    """Test UserProfile model."""

    def test_profile_created_on_user_creation(self, user):
        """Test that profile is created when user is created."""
        assert hasattr(user, 'profile')
        assert user.profile is not None

    def test_profile_update(self, user_with_profile):
        """Test updating user profile."""
        profile = user_with_profile.profile
        profile.company = 'New Company'
        profile.save()

        profile.refresh_from_db()
        assert profile.company == 'New Company'
