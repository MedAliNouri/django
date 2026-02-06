"""
Keycloak authentication API views.
"""

import logging

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.keycloak_utils import KeycloakClient, get_or_create_user_from_keycloak, sync_user_with_keycloak
from apps.users.api.v1.serializers import UserDetailSerializer

from .keycloak_serializers import (
    KeycloakLoginSerializer,
    KeycloakLogoutSerializer,
    KeycloakRefreshSerializer,
    KeycloakTokenResponseSerializer,
    KeycloakUserInfoSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema_view(
    post=extend_schema(
        summary='Login with Keycloak',
        description='Authenticate user with Keycloak credentials and get access/refresh tokens',
        request=KeycloakLoginSerializer,
        responses={
            200: KeycloakTokenResponseSerializer,
            400: {'description': 'Invalid credentials'},
            500: {'description': 'Keycloak server error'},
        },
        tags=['Authentication - Keycloak'],
    )
)
class KeycloakLoginView(APIView):
    """
    Authenticate user with Keycloak and return tokens.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = KeycloakLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        try:
            # Exchange credentials for Keycloak tokens
            client = KeycloakClient()
            token_response = client.exchange_token(username, password)

            # Decode token to get user info
            payload = client.decode_token(token_response['access_token'], verify=True)

            # Get or create Django user
            user = get_or_create_user_from_keycloak(payload)

            # Prepare response
            response_data = {
                'access_token': token_response['access_token'],
                'refresh_token': token_response['refresh_token'],
                'expires_in': token_response['expires_in'],
                'refresh_expires_in': token_response.get('refresh_expires_in'),
                'token_type': token_response.get('token_type', 'Bearer'),
                'user': UserDetailSerializer(user).data,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f'Keycloak login failed: {e}')
            return Response(
                {'error': 'Authentication failed', 'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema_view(
    post=extend_schema(
        summary='Refresh Keycloak token',
        description='Refresh an expired access token using refresh token',
        request=KeycloakRefreshSerializer,
        responses={
            200: KeycloakTokenResponseSerializer,
            400: {'description': 'Invalid or expired refresh token'},
        },
        tags=['Authentication - Keycloak'],
    )
)
class KeycloakRefreshView(APIView):
    """
    Refresh Keycloak access token using refresh token.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = KeycloakRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data['refresh_token']

        try:
            client = KeycloakClient()
            token_response = client.refresh_token(refresh_token)

            # Decode new token to get user info
            payload = client.decode_token(token_response['access_token'], verify=True)

            # Get or update user
            user = get_or_create_user_from_keycloak(payload)

            response_data = {
                'access_token': token_response['access_token'],
                'refresh_token': token_response['refresh_token'],
                'expires_in': token_response['expires_in'],
                'refresh_expires_in': token_response.get('refresh_expires_in'),
                'token_type': token_response.get('token_type', 'Bearer'),
                'user': UserDetailSerializer(user).data,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f'Token refresh failed: {e}')
            return Response(
                {'error': 'Token refresh failed', 'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema_view(
    post=extend_schema(
        summary='Logout from Keycloak',
        description='Invalidate refresh token and logout user',
        request=KeycloakLogoutSerializer,
        responses={
            200: {'description': 'Successfully logged out'},
            400: {'description': 'Logout failed'},
        },
        tags=['Authentication - Keycloak'],
    )
)
class KeycloakLogoutView(APIView):
    """
    Logout user by invalidating Keycloak refresh token.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = KeycloakLogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data['refresh_token']

        try:
            client = KeycloakClient()
            client.logout(refresh_token)

            return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f'Logout failed: {e}')
            return Response({'error': 'Logout failed', 'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(
        summary='Get Keycloak user info',
        description='Get user information from Keycloak using access token',
        responses={
            200: KeycloakUserInfoSerializer,
            401: {'description': 'Invalid or expired token'},
        },
        tags=['Authentication - Keycloak'],
    )
)
class KeycloakUserInfoView(APIView):
    """
    Get user info from Keycloak using access token.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return Response({'error': 'No bearer token provided'}, status=status.HTTP_401_UNAUTHORIZED)

        token = auth_header.split(' ')[1]

        try:
            client = KeycloakClient()
            user_info = client.get_user_info(token)

            # Sync Django user with Keycloak
            sync_user_with_keycloak(request.user, token)

            return Response(user_info, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f'Failed to get user info: {e}')
            return Response({'error': 'Failed to get user info', 'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(
        summary='Get Keycloak configuration',
        description='Get Keycloak server configuration for frontend clients',
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'server_url': {'type': 'string'},
                    'realm': {'type': 'string'},
                    'client_id': {'type': 'string'},
                    'authorization_url': {'type': 'string'},
                    'token_url': {'type': 'string'},
                    'userinfo_url': {'type': 'string'},
                    'logout_url': {'type': 'string'},
                },
            }
        },
        tags=['Authentication - Keycloak'],
    )
)
class KeycloakConfigView(APIView):
    """
    Get Keycloak configuration for frontend clients.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        from django.conf import settings

        config_data = {
            'server_url': settings.KEYCLOAK_SERVER_URL,
            'realm': settings.KEYCLOAK_REALM,
            'client_id': settings.KEYCLOAK_CLIENT_ID,
            'authorization_url': settings.KEYCLOAK_AUTHORIZATION_URL,
            'token_url': settings.KEYCLOAK_TOKEN_URL,
            'userinfo_url': settings.KEYCLOAK_USERINFO_URL,
            'logout_url': settings.KEYCLOAK_LOGOUT_URL,
        }

        return Response(config_data, status=status.HTTP_200_OK)
