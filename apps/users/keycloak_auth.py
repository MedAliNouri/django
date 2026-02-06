"""
Keycloak authentication backend and DRF authentication classes.
"""

import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from rest_framework import authentication, exceptions

from .keycloak_utils import get_or_create_user_from_keycloak, validate_keycloak_token

logger = logging.getLogger(__name__)
User = get_user_model()


class KeycloakAuthenticationBackend(BaseBackend):
    """
    Django authentication backend for Keycloak.

    This allows using authenticate() with Keycloak tokens.
    """

    def authenticate(self, request, token=None, **kwargs):
        """
        Authenticate user using Keycloak token.

        Args:
            request: HTTP request object
            token: Keycloak access token

        Returns:
            User instance if authentication successful, None otherwise
        """
        if not token:
            return None

        try:
            # Validate token with Keycloak
            payload = validate_keycloak_token(token)
            if not payload:
                return None

            # Get or create user from token
            user = get_or_create_user_from_keycloak(payload)
            return user
        except Exception as e:
            logger.error(f'Keycloak authentication failed: {e}')
            return None

    def get_user(self, user_id):
        """
        Get user by ID for session authentication.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class KeycloakJWTAuthentication(authentication.BaseAuthentication):
    """
    DRF authentication class for Keycloak JWT tokens.

    Expects Authorization header: Bearer <keycloak_token>
    """

    keyword = 'Bearer'

    def authenticate(self, request):
        """
        Authenticate request using Keycloak JWT token.

        Args:
            request: DRF request object

        Returns:
            Tuple of (user, token) if successful, None otherwise
        """
        auth_header = authentication.get_authorization_header(request).decode('utf-8')

        if not auth_header:
            return None

        auth_parts = auth_header.split()

        if len(auth_parts) == 0:
            return None

        if auth_parts[0].lower() != self.keyword.lower():
            return None

        if len(auth_parts) == 1:
            raise exceptions.AuthenticationFailed('Invalid token header. No credentials provided.')

        if len(auth_parts) > 2:
            raise exceptions.AuthenticationFailed('Invalid token header. Token string should not contain spaces.')

        token = auth_parts[1]

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, token):
        """
        Validate Keycloak token and return user.

        Args:
            token: JWT token string

        Returns:
            Tuple of (user, token)

        Raises:
            AuthenticationFailed: If token is invalid
        """
        try:
            # Validate token with Keycloak
            payload = validate_keycloak_token(token)

            if not payload:
                raise exceptions.AuthenticationFailed('Invalid or expired token')

            # Check if token is active
            if not payload.get('active', True):
                raise exceptions.AuthenticationFailed('Token is not active')

            # Get or create user from token
            user = get_or_create_user_from_keycloak(payload)

            if not user.is_active:
                raise exceptions.AuthenticationFailed('User account is disabled')

            return (user, token)

        except exceptions.AuthenticationFailed:
            raise
        except Exception as e:
            logger.error(f'Token authentication failed: {e}')
            raise exceptions.AuthenticationFailed('Could not authenticate with provided token')

    def authenticate_header(self, request):
        """
        Return WWW-Authenticate header for 401 responses.
        """
        return self.keyword


class HybridAuthentication(authentication.BaseAuthentication):
    """
    Hybrid authentication supporting both Keycloak JWT and Django JWT tokens.

    This tries Keycloak authentication first, then falls back to Django JWT.
    """

    def authenticate(self, request):
        """
        Try Keycloak authentication first, then Django JWT.
        """
        # Try Keycloak authentication
        keycloak_auth = KeycloakJWTAuthentication()
        try:
            result = keycloak_auth.authenticate(request)
            if result is not None:
                return result
        except exceptions.AuthenticationFailed:
            pass  # Fall through to Django JWT

        # Try Django JWT authentication
        from rest_framework_simplejwt.authentication import JWTAuthentication

        jwt_auth = JWTAuthentication()
        try:
            result = jwt_auth.authenticate(request)
            if result is not None:
                return result
        except exceptions.AuthenticationFailed:
            pass

        return None

    def authenticate_header(self, request):
        return 'Bearer'
