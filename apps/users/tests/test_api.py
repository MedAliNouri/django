"""
Tests for User API endpoints.
"""

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestUserAPI:
    """Test User API endpoints."""

    def test_create_user(self, api_client):
        """Test user registration."""
        url = reverse('v1:user-list')
        data = {
            'email': 'newuser@example.com',
            'password': 'NewPass123!',
            'password_confirm': 'NewPass123!',
            'first_name': 'New',
            'last_name': 'User',
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert response.data['data']['email'] == data['email']

    def test_create_user_password_mismatch(self, api_client):
        """Test registration with mismatched passwords."""
        url = reverse('v1:user-list')
        data = {
            'email': 'newuser@example.com',
            'password': 'NewPass123!',
            'password_confirm': 'DifferentPass123!',
            'first_name': 'New',
            'last_name': 'User',
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False

    def test_list_users(self, authenticated_client, user, active_user):
        """Test listing users."""
        url = reverse('v1:user-list')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['data']) >= 2

    def test_retrieve_user(self, authenticated_client, user):
        """Test retrieving user details."""
        url = reverse('v1:user-detail', kwargs={'pk': user.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['email'] == user.email

    def test_update_user(self, authenticated_client, user):
        """Test updating user."""
        url = reverse('v1:user-detail', kwargs={'pk': user.id})
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
        }

        response = authenticated_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['first_name'] == 'Updated'

    def test_get_me(self, authenticated_client, user):
        """Test getting current user info."""
        url = reverse('v1:user-me')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['email'] == user.email

    def test_change_password(self, authenticated_client, user):
        """Test changing password."""
        url = reverse('v1:user-change-password')
        data = {
            'old_password': 'TestPass123!',
            'new_password': 'NewPass456!',
            'new_password_confirm': 'NewPass456!',
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True

        # Verify password changed
        user.refresh_from_db()
        assert user.check_password('NewPass456!')

    def test_user_stats(self, authenticated_client, user, active_user):
        """Test user statistics endpoint."""
        url = reverse('v1:user-stats')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'total' in response.data['data']
        assert 'active' in response.data['data']


@pytest.mark.django_db
class TestAuthenticationAPI:
    """Test authentication endpoints."""

    def test_login(self, api_client, user):
        """Test user login."""
        url = reverse('v1:token_obtain_pair')
        data = {
            'email': user.email,
            'password': 'TestPass123!',
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_login_invalid_credentials(self, api_client, user):
        """Test login with invalid credentials."""
        url = reverse('v1:token_obtain_pair')
        data = {
            'email': user.email,
            'password': 'WrongPassword',
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token(self, api_client, user):
        """Test refreshing access token."""
        # First login to get tokens
        login_url = reverse('v1:token_obtain_pair')
        login_data = {
            'email': user.email,
            'password': 'TestPass123!',
        }
        login_response = api_client.post(login_url, login_data)
        refresh_token = login_response.data['refresh']

        # Refresh token
        refresh_url = reverse('v1:token_refresh')
        refresh_data = {'refresh': refresh_token}
        response = api_client.post(refresh_url, refresh_data)

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
