"""
Serializers for Keycloak authentication endpoints.
"""

from rest_framework import serializers


class KeycloakLoginSerializer(serializers.Serializer):
    """
    Serializer for Keycloak login endpoint.
    """

    username = serializers.CharField(required=True, help_text='Username or email')
    password = serializers.CharField(required=True, write_only=True, help_text='User password')


class KeycloakRefreshSerializer(serializers.Serializer):
    """
    Serializer for Keycloak token refresh endpoint.
    """

    refresh_token = serializers.CharField(required=True, help_text='Keycloak refresh token')


class KeycloakLogoutSerializer(serializers.Serializer):
    """
    Serializer for Keycloak logout endpoint.
    """

    refresh_token = serializers.CharField(required=True, help_text='Keycloak refresh token to invalidate')


class KeycloakTokenResponseSerializer(serializers.Serializer):
    """
    Serializer for Keycloak token response.
    """

    access_token = serializers.CharField(help_text='JWT access token')
    refresh_token = serializers.CharField(help_text='JWT refresh token')
    expires_in = serializers.IntegerField(help_text='Access token expiration time in seconds')
    refresh_expires_in = serializers.IntegerField(
        required=False, help_text='Refresh token expiration time in seconds'
    )
    token_type = serializers.CharField(default='Bearer', help_text='Token type')
    user = serializers.DictField(help_text='User information')


class KeycloakUserInfoSerializer(serializers.Serializer):
    """
    Serializer for Keycloak user info response.
    """

    sub = serializers.CharField(help_text='Keycloak user ID')
    email = serializers.EmailField(help_text='User email')
    email_verified = serializers.BooleanField(help_text='Whether email is verified')
    preferred_username = serializers.CharField(help_text='Preferred username')
    given_name = serializers.CharField(required=False, help_text='First name')
    family_name = serializers.CharField(required=False, help_text='Last name')
    name = serializers.CharField(required=False, help_text='Full name')
