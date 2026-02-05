"""
Pytest fixtures for user tests.

This module provides reusable test fixtures for the users app.
"""

import pytest
from django.contrib.auth import get_user_model

from apps.users.models import UserProfile

User = get_user_model()


@pytest.fixture
def user_data():
    """Sample user data for tests."""
    return {
        'email': 'test@example.com',
        'password': 'TestPass123!',
        'first_name': 'Test',
        'last_name': 'User',
    }


@pytest.fixture
def user(db, user_data):
    """Create a test user."""
    return User.objects.create_user(**user_data)


@pytest.fixture
def active_user(db):
    """Create an active verified user."""
    return User.objects.create_user(
        email='active@example.com',
        password='TestPass123!',
        first_name='Active',
        last_name='User',
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def staff_user(db):
    """Create a staff user."""
    return User.objects.create_user(
        email='staff@example.com',
        password='TestPass123!',
        first_name='Staff',
        last_name='User',
        is_staff=True,
    )


@pytest.fixture
def superuser(db):
    """Create a superuser."""
    return User.objects.create_superuser(
        email='admin@example.com',
        password='AdminPass123!',
        first_name='Admin',
        last_name='User',
    )


@pytest.fixture
def user_with_profile(db, user):
    """Create a user with profile."""
    UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'company': 'Test Company',
            'job_title': 'Software Engineer',
            'location': 'San Francisco, CA',
        },
    )
    return user


@pytest.fixture
def api_client():
    """DRF API client."""
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client
