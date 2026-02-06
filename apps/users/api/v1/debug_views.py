"""
Debug views for Keycloak authentication troubleshooting.
"""

import logging

from django.conf import settings
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


@extend_schema_view(
    post=extend_schema(
        summary='Debug Keycloak Token',
        description='Debug endpoint to test Keycloak token validation and show detailed error information',
        request={
            'application/json': {
                'type': 'object',
                'properties': {'token': {'type': 'string', 'description': 'Keycloak JWT token'}},
                'required': ['token'],
            }
        },
        responses={200: {'description': 'Token validation details'}},
        tags=['Debug - Keycloak'],
    )
)
class KeucloakTokenDebugView(APIView):
    """
    Debug endpoint to validate Keycloak tokens and show detailed information.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')

        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)

        debug_info = {
            'token_received': True,
            'token_length': len(token),
            'token_preview': f'{token[:50]}...',
            'keycloak_config': {
                'server_url': settings.KEYCLOAK_SERVER_URL,
                'realm': settings.KEYCLOAK_REALM,
                'client_id': settings.KEYCLOAK_CLIENT_ID,
                'client_secret_set': bool(settings.KEYCLOAK_CLIENT_SECRET),
            },
            'validation_steps': {},
        }

        # Step 1: Try to decode token without verification (to see claims)
        try:
            import jwt

            unverified_payload = jwt.decode(token, options={'verify_signature': False})
            debug_info['validation_steps']['1_decode_unverified'] = {
                'success': True,
                'payload': unverified_payload,
            }
        except Exception as e:
            debug_info['validation_steps']['1_decode_unverified'] = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
            }
            return Response(debug_info, status=status.HTTP_200_OK)

        # Step 2: Check token claims
        required_claims = ['email', 'sub', 'exp', 'iat']
        missing_claims = [claim for claim in required_claims if claim not in unverified_payload]

        debug_info['validation_steps']['2_check_claims'] = {
            'success': len(missing_claims) == 0,
            'has_email': 'email' in unverified_payload,
            'email': unverified_payload.get('email'),
            'issuer': unverified_payload.get('iss'),
            'audience': unverified_payload.get('aud'),
            'subject': unverified_payload.get('sub'),
            'missing_claims': missing_claims,
        }

        # Step 3: Check Keycloak server accessibility
        try:
            import requests

            jwks_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/certs"
            response = requests.get(jwks_url, timeout=5)

            debug_info['validation_steps']['3_keycloak_connectivity'] = {
                'success': response.status_code == 200,
                'jwks_url': jwks_url,
                'status_code': response.status_code,
                'accessible': True,
            }
        except Exception as e:
            debug_info['validation_steps']['3_keycloak_connectivity'] = {
                'success': False,
                'jwks_url': jwks_url,
                'error': str(e),
                'error_type': type(e).__name__,
                'accessible': False,
            }

        # Step 4: Try to validate token with Keycloak
        try:
            from apps.users.keycloak_utils import validate_keycloak_token

            payload = validate_keycloak_token(token)

            if payload:
                debug_info['validation_steps']['4_validate_with_keycloak'] = {
                    'success': True,
                    'payload': payload,
                    'user_email': payload.get('email'),
                }
            else:
                debug_info['validation_steps']['4_validate_with_keycloak'] = {
                    'success': False,
                    'error': 'Token validation returned None',
                }
        except Exception as e:
            debug_info['validation_steps']['4_validate_with_keycloak'] = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
            }

        # Step 5: Try to create/get user
        if debug_info['validation_steps'].get('4_validate_with_keycloak', {}).get('success'):
            try:
                from apps.users.keycloak_utils import get_or_create_user_from_keycloak

                payload = debug_info['validation_steps']['4_validate_with_keycloak']['payload']
                user = get_or_create_user_from_keycloak(payload)

                debug_info['validation_steps']['5_create_user'] = {
                    'success': True,
                    'user_id': str(user.id),
                    'user_email': user.email,
                    'user_created': True,
                }
            except Exception as e:
                debug_info['validation_steps']['5_create_user'] = {
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__,
                }

        # Summary
        all_steps_success = all(
            step.get('success', False) for step in debug_info['validation_steps'].values() if 'success' in step
        )

        debug_info['summary'] = {
            'all_steps_passed': all_steps_success,
            'recommendation': self._get_recommendation(debug_info),
        }

        return Response(debug_info, status=status.HTTP_200_OK)

    def _get_recommendation(self, debug_info):
        """Get recommendation based on debug results."""
        steps = debug_info['validation_steps']

        if not steps.get('1_decode_unverified', {}).get('success'):
            return 'Token is malformed. Ensure you are sending a valid JWT token.'

        if not steps.get('2_check_claims', {}).get('success'):
            return 'Token is missing required claims. Check Keycloak client scope configuration.'

        if not steps.get('3_keycloak_connectivity', {}).get('success'):
            return 'Cannot connect to Keycloak server. Check KEYCLOAK_SERVER_URL in settings and ensure Keycloak is running.'

        if not steps.get('4_validate_with_keycloak', {}).get('success'):
            error = steps['4_validate_with_keycloak'].get('error', '')
            if 'expired' in error.lower():
                return 'Token has expired. Request a new token from Keycloak.'
            elif 'signature' in error.lower():
                return 'Token signature verification failed. Check KEYCLOAK_CLIENT_ID and realm configuration.'
            return f"Token validation failed: {error}"

        if not steps.get('5_create_user', {}).get('success'):
            return 'Token is valid but user creation failed. Check Django logs for database errors.'

        return 'All validation steps passed! Token should work with /me endpoint.'
