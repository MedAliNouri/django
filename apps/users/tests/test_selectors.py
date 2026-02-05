"""
Tests for User selectors.
"""

import pytest

from apps.users import selectors


@pytest.mark.django_db
class TestUserSelectors:
    """Test User selectors."""

    def test_get_user_by_id(self, user):
        """Test getting user by ID."""
        found = selectors.get_user_by_id(user.id)
        assert found == user

    def test_get_user_by_email(self, user):
        """Test getting user by email."""
        found = selectors.get_user_by_email(user.email)
        assert found == user

    def test_user_exists(self, user):
        """Test checking if user exists."""
        assert selectors.user_exists(user.email) is True
        assert selectors.user_exists('nonexistent@example.com') is False

    def test_get_user_list(self, user, active_user, staff_user):
        """Test getting user list."""
        users = selectors.get_user_list()
        assert users.count() == 3

    def test_get_user_list_filtered(self, user, active_user):
        """Test getting filtered user list."""
        # Filter by active
        active_users = selectors.get_user_list(is_active=True)
        assert user in active_users
        assert active_user in active_users

        # Filter by verified
        verified_users = selectors.get_user_list(is_verified=True)
        assert active_user in verified_users
        assert user not in verified_users

    def test_search_users(self, user, active_user):
        """Test searching users."""
        results = selectors.search_users('test')
        assert user in results

        results = selectors.search_users('active')
        assert active_user in results

    def test_get_user_stats(self, user, active_user, staff_user):
        """Test getting user statistics."""
        stats = selectors.get_user_stats()

        assert stats['total'] == 3
        assert stats['active'] >= 1
        assert 'verified' in stats
        assert 'staff' in stats

    def test_is_email_available(self, user):
        """Test checking email availability."""
        assert selectors.is_email_available(user.email) is False
        assert selectors.is_email_available('available@example.com') is True
