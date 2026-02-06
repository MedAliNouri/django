"""
Keycloak utility functions for authentication and token validation.
"""

import logging
from typing import Optional

import jwt
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from jwt import PyJWKClient
from keycloak import KeycloakOpenID

logger = logging.getLogger(__name__)
User = get_user_model()


class KeycloakClient:
    """
    Keycloak client for handling authentication and token operations.
    """

    def __init__(self):
        self.server_url = settings.KEYCLOAK_SERVER_URL
        self.realm = settings.KEYCLOAK_REALM
        self.client_id = settings.KEYCLOAK_CLIENT_ID
        self.client_secret = settings.KEYCLOAK_CLIENT_SECRET

        self.keycloak_openid = KeycloakOpenID(
            server_url=self.server_url,
            realm_name=self.realm,
            client_id=self.client_id,
            client_secret_key=self.client_secret,
        )

    def get_public_key(self) -> str:
        """
        Get the Keycloak realm public key for token validation.
        """
        try:
            return self.keycloak_openid.public_key()
        except Exception as e:
            logger.error(f'Failed to get Keycloak public key: {e}')
            raise

    def exchange_token(self, username: str, password: str) -> dict:
        """
        Exchange username/password for Keycloak tokens.

        Returns dict with access_token, refresh_token, expires_in, etc.
        """
        try:
            token = self.keycloak_openid.token(username, password)
            return token
        except Exception as e:
            logger.error(f'Failed to exchange credentials for token: {e}')
            raise

    def refresh_token(self, refresh_token: str) -> dict:
        """
        Refresh an expired access token using refresh token.
        """
        try:
            return self.keycloak_openid.refresh_token(refresh_token)
        except Exception as e:
            logger.error(f'Failed to refresh token: {e}')
            raise

    def logout(self, refresh_token: str) -> bool:
        """
        Logout user by invalidating refresh token.
        """
        try:
            self.keycloak_openid.logout(refresh_token)
            return True
        except Exception as e:
            logger.error(f'Failed to logout: {e}')
            return False

    def introspect_token(self, token: str) -> dict:
        """
        Introspect token to check if it's valid and active.
        """
        try:
            return self.keycloak_openid.introspect(token)
        except Exception as e:
            logger.error(f'Failed to introspect token: {e}')
            raise

    def get_user_info(self, token: str) -> dict:
        """
        Get user information from Keycloak using access token.
        """
        try:
            return self.keycloak_openid.userinfo(token)
        except Exception as e:
            logger.error(f'Failed to get user info: {e}')
            raise

    def decode_token(self, token: str, verify: bool = True) -> dict:
        """
        Decode and validate JWT token from Keycloak.

        Args:
            token: JWT token string
            verify: Whether to verify token signature

        Returns:
            Decoded token payload
        """
        try:
            if verify:
                # Get JWKS URL for public key
                jwks_url = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/certs"
                jwks_client = PyJWKClient(jwks_url)
                signing_key = jwks_client.get_signing_key_from_jwt(token)

                # Decode and verify token
                payload = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=['RS256'],
                    audience=self.client_id,
                    options={'verify_exp': True, 'verify_aud': True},
                )
            else:
                # Decode without verification (for debugging only)
                payload = jwt.decode(token, options={'verify_signature': False})

            return payload
        except jwt.ExpiredSignatureError:
            logger.error('Token has expired')
            raise
        except jwt.InvalidTokenError as e:
            logger.error(f'Invalid token: {e}')
            raise

    def create_user(self, user_data: dict) -> dict:
        """
        Create a new user in Keycloak.

        Args:
            user_data: Dictionary with user information (email, firstName, lastName, etc.)

        Returns:
            Created user data
        """
        try:
            # This requires admin credentials - you may need to use KeycloakAdmin
            from keycloak import KeycloakAdmin

            keycloak_admin = KeycloakAdmin(
                server_url=self.server_url,
                realm_name=self.realm,
                client_id=self.client_id,
                client_secret_key=self.client_secret,
            )

            user_id = keycloak_admin.create_user(user_data)
            return {'id': user_id, **user_data}
        except Exception as e:
            logger.error(f'Failed to create user in Keycloak: {e}')
            raise


def validate_keycloak_token(token: str) -> Optional[dict]:
    """
    Validate Keycloak JWT token and return decoded payload.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        client = KeycloakClient()
        payload = client.decode_token(token, verify=True)
        return payload
    except Exception as e:
        logger.error(f'Token validation failed: {e}')
        return None


def get_or_create_user_from_keycloak(token_payload: dict) -> User:
    """
    Get or create Django user from Keycloak token payload.

    Args:
        token_payload: Decoded JWT token payload from Keycloak

    Returns:
        User instance
    """
    email = token_payload.get('email')
    if not email:
        raise ValueError('Email not found in token payload')

    # Extract user information from token
    first_name = token_payload.get('given_name', '')
    last_name = token_payload.get('family_name', '')
    is_email_verified = token_payload.get('email_verified', False)
    keycloak_id = token_payload.get('sub')  # Keycloak user ID

    # Get or create user
    user, created = User.objects.get_or_create(
        email=email, defaults={'first_name': first_name, 'last_name': last_name, 'is_active': True}
    )

    # Update user information if exists
    if not created:
        update_fields = []
        if user.first_name != first_name:
            user.first_name = first_name
            update_fields.append('first_name')
        if user.last_name != last_name:
            user.last_name = last_name
            update_fields.append('last_name')
        if user.is_verified != is_email_verified:
            user.is_verified = is_email_verified
            update_fields.append('is_verified')

        if update_fields:
            user.save(update_fields=update_fields)

    # Store Keycloak ID in user profile if needed
    if hasattr(user, 'profile') and keycloak_id:
        profile = user.profile
        if not hasattr(profile, 'keycloak_id') or profile.keycloak_id != keycloak_id:
            # You may need to add a keycloak_id field to UserProfile model
            pass

    logger.info(f"User {email} {'created' if created else 'retrieved'} from Keycloak token")
    return user


def sync_user_with_keycloak(user: User, access_token: str) -> User:
    """
    Sync Django user data with Keycloak user info.

    Args:
        user: Django User instance
        access_token: Keycloak access token

    Returns:
        Updated User instance
    """
    try:
        client = KeycloakClient()
        user_info = client.get_user_info(access_token)

        # Update user fields
        update_fields = []
        if user_info.get('given_name') and user.first_name != user_info['given_name']:
            user.first_name = user_info['given_name']
            update_fields.append('first_name')

        if user_info.get('family_name') and user.last_name != user_info['family_name']:
            user.last_name = user_info['family_name']
            update_fields.append('family_name')

        if user_info.get('email_verified') is not None and user.is_verified != user_info['email_verified']:
            user.is_verified = user_info['email_verified']
            update_fields.append('is_verified')

        if update_fields:
            user.save(update_fields=update_fields)
            logger.info(f'User {user.email} synced with Keycloak')

        return user
    except Exception as e:
        logger.error(f'Failed to sync user with Keycloak: {e}')
        return user
