"""
Keycloak authentication middleware for automatic user sync.

This middleware intercepts requests with Keycloak tokens and automatically
creates/updates Django users on the fly.
"""

import logging

from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin

from apps.users.keycloak_utils import get_or_create_user_from_keycloak, validate_keycloak_token

logger = logging.getLogger(__name__)
User = get_user_model()


class KeycloakAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware that automatically authenticates users via Keycloak tokens.

    This middleware:
    1. Checks for Bearer token in Authorization header
    2. Validates token with Keycloak
    3. Automatically creates/updates Django user from token
    4. Attaches user to request
    """

    def process_request(self, request):
        """
        Process incoming request and authenticate via Keycloak if token present.
        """
        # Skip if user is already authenticated via Django session
        if hasattr(request, 'user') and request.user.is_authenticated:
            return None

        # Get Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        # Extract token
        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            return None

        # Validate token and get user
        try:
            # Validate Keycloak token
            payload = validate_keycloak_token(token)

            if not payload:
                logger.debug('Invalid Keycloak token')
                return None

            # Get or create user from Keycloak token
            user = get_or_create_user_from_keycloak(payload)

            if user and user.is_active:
                # Attach user to request
                request.user = user
                request.keycloak_token = token
                request.keycloak_payload = payload
                logger.info(f'User {user.email} authenticated via Keycloak middleware')

        except Exception as e:
            logger.error(f'Keycloak authentication middleware error: {e}')
            # Don't block the request, let DRF auth handle it
            return None

        return None
