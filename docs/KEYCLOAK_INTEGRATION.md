# Keycloak Integration Guide

This document describes how to integrate and use Keycloak authentication with the Django REST Framework application.

## Overview

The application supports **hybrid authentication** with both:
- **Django JWT** (default) - For internal user management
- **Keycloak SSO** - For enterprise single sign-on integration

Users can authenticate using either method, and the system automatically creates Django user accounts from Keycloak tokens.

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Client    │────────>│    Django    │────────>│  Keycloak   │
│  Frontend   │<────────│   Backend    │<────────│   Server    │
└─────────────┘         └──────────────┘         └─────────────┘
     │                        │
     │                        │
     └────────────────────────┘
         JWT Token Flow
```

### Components

1. **KeycloakClient** (`apps/users/keycloak_utils.py`)
   - Handles communication with Keycloak server
   - Token validation and exchange
   - User info retrieval

2. **KeycloakAuthenticationBackend** (`apps/users/keycloak_auth.py`)
   - Django authentication backend for Keycloak
   - Integrates with Django's authentication system

3. **KeycloakJWTAuthentication** (`apps/users/keycloak_auth.py`)
   - DRF authentication class for API endpoints
   - Validates Keycloak JWT tokens

4. **HybridAuthentication** (`apps/users/keycloak_auth.py`)
   - Supports both Keycloak and Django JWT
   - Tries Keycloak first, falls back to Django JWT

## Configuration

### Environment Variables

Add these variables to your `.env` file:

```bash
# Keycloak Configuration
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=your-realm-name
KEYCLOAK_CLIENT_ID=your-client-id
KEYCLOAK_CLIENT_SECRET=your-client-secret
```

### Keycloak Server Setup

1. **Create a Realm** (or use existing)
   ```
   Keycloak Admin Console > Create Realm > Name: "your-realm-name"
   ```

2. **Create a Client**
   ```
   Clients > Create Client
   - Client ID: django-client
   - Client Protocol: openid-connect
   - Access Type: confidential
   - Valid Redirect URIs: http://localhost:8000/*
   - Web Origins: http://localhost:8000
   ```

3. **Get Client Secret**
   ```
   Clients > django-client > Credentials Tab
   Copy the "Secret" value and add to KEYCLOAK_CLIENT_SECRET
   ```

4. **Configure Client Scopes**
   ```
   Clients > django-client > Client Scopes
   Enable: email, profile, roles
   ```

5. **Create Test User**
   ```
   Users > Add User
   - Username: testuser
   - Email: test@example.com
   - First Name: Test
   - Last Name: User

   Then set password:
   Users > testuser > Credentials > Set Password
   ```

## API Endpoints

### 1. Keycloak Login

Authenticate with Keycloak credentials and get tokens.

**Endpoint:** `POST /api/v1/auth/keycloak/login/`

**Request:**
```json
{
  "username": "testuser",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 300,
  "refresh_expires_in": 1800,
  "token_type": "Bearer",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "is_active": true
  }
}
```

### 2. Refresh Token

Refresh an expired access token.

**Endpoint:** `POST /api/v1/auth/keycloak/refresh/`

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** Same as login response with new tokens

### 3. Logout

Invalidate refresh token and logout.

**Endpoint:** `POST /api/v1/auth/keycloak/logout/`

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

### 4. Get User Info

Get user information from Keycloak.

**Endpoint:** `GET /api/v1/auth/keycloak/userinfo/`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "sub": "f8e7d6c5-b4a3-9281-7654-321098765432",
  "email": "test@example.com",
  "email_verified": true,
  "preferred_username": "testuser",
  "given_name": "Test",
  "family_name": "User",
  "name": "Test User"
}
```

### 5. Get Keycloak Config

Get Keycloak configuration for frontend clients.

**Endpoint:** `GET /api/v1/auth/keycloak/config/`

**Response:**
```json
{
  "server_url": "http://localhost:8080",
  "realm": "your-realm-name",
  "client_id": "django-client",
  "authorization_url": "http://localhost:8080/realms/your-realm-name/protocol/openid-connect/auth",
  "token_url": "http://localhost:8080/realms/your-realm-name/protocol/openid-connect/token",
  "userinfo_url": "http://localhost:8080/realms/your-realm-name/protocol/openid-connect/userinfo",
  "logout_url": "http://localhost:8080/realms/your-realm-name/protocol/openid-connect/logout"
}
```

## Usage Examples

### Python/Requests

```python
import requests

# Login
response = requests.post(
    'http://localhost:8000/api/v1/auth/keycloak/login/',
    json={
        'username': 'testuser',
        'password': 'password123'
    }
)
data = response.json()
access_token = data['access_token']

# Make authenticated request
response = requests.get(
    'http://localhost:8000/api/v1/users/me/',
    headers={'Authorization': f'Bearer {access_token}'}
)
```

### cURL

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/keycloak/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'

# Use token
curl -X GET http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### JavaScript/Fetch

```javascript
// Login
const loginResponse = await fetch('http://localhost:8000/api/v1/auth/keycloak/login/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'testuser',
    password: 'password123'
  })
});

const { access_token } = await loginResponse.json();

// Make authenticated request
const userResponse = await fetch('http://localhost:8000/api/v1/users/me/', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
```

## Hybrid Authentication

The application supports both authentication methods simultaneously. You can use either:

1. **Django JWT tokens** from `/api/v1/auth/login/`
2. **Keycloak tokens** from `/api/v1/auth/keycloak/login/`

Both token types work with the same API endpoints when using `HybridAuthentication`.

### Switching to Hybrid Mode

To enable hybrid authentication for all endpoints, update `config/settings/base.py`:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.users.keycloak_auth.HybridAuthentication',  # Try Keycloak, then Django JWT
    ],
    # ... other settings
}
```

## User Synchronization

When a user logs in via Keycloak:

1. Django validates the Keycloak token
2. Extracts user information (email, name, etc.)
3. Creates a Django user if it doesn't exist
4. Updates existing user information if changed
5. Returns both the Keycloak token and Django user data

### User Mapping

| Keycloak Field | Django Field |
|----------------|--------------|
| `email` | `email` |
| `given_name` | `first_name` |
| `family_name` | `last_name` |
| `email_verified` | `is_verified` |
| `sub` (user ID) | Stored in profile (optional) |

## Security Considerations

1. **Token Validation**
   - All Keycloak tokens are validated using RS256 with public keys from JWKS
   - Token expiration is strictly enforced
   - Audience (client_id) is verified

2. **HTTPS in Production**
   - Always use HTTPS in production
   - Configure Keycloak with valid SSL certificates
   - Update `KEYCLOAK_SERVER_URL` to use `https://`

3. **Client Secret**
   - Keep `KEYCLOAK_CLIENT_SECRET` secure
   - Never commit to version control
   - Rotate secrets periodically

4. **CORS Configuration**
   - Update `CORS_ALLOWED_ORIGINS` in settings
   - Configure Keycloak's "Web Origins" to match

## Troubleshooting

### Token Validation Fails

**Error:** `Invalid or expired token`

**Solutions:**
- Check token expiration
- Verify `KEYCLOAK_SERVER_URL` is correct and accessible
- Ensure Keycloak server is running
- Check client configuration in Keycloak

### User Creation Fails

**Error:** `Email not found in token payload`

**Solutions:**
- Enable "email" scope for the client
- Check user has email set in Keycloak
- Verify email is included in token claims

### Connection Refused

**Error:** `Failed to connect to Keycloak`

**Solutions:**
- Check `KEYCLOAK_SERVER_URL` is correct
- Ensure Keycloak server is accessible from Django container
- If Keycloak is on host machine, use `host.docker.internal` instead of `localhost`

### Invalid Client Credentials

**Error:** `Invalid client or Invalid client credentials`

**Solutions:**
- Verify `KEYCLOAK_CLIENT_ID` matches client ID in Keycloak
- Check `KEYCLOAK_CLIENT_SECRET` is correct
- Ensure client type is "confidential" in Keycloak

## Testing

### Unit Tests

```python
from django.test import TestCase
from apps.users.keycloak_utils import validate_keycloak_token

class KeycloakAuthTest(TestCase):
    def test_token_validation(self):
        # Mock Keycloak token
        token = "mock_token"
        result = validate_keycloak_token(token)
        # Add assertions
```

### Integration Tests

```bash
# Test Keycloak login endpoint
pytest apps/users/tests/test_keycloak_auth.py -v
```

## Additional Resources

- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [OpenID Connect Specification](https://openid.net/connect/)
- [python-keycloak Library](https://python-keycloak.readthedocs.io/)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)

## Support

For issues or questions:
1. Check Keycloak server logs
2. Check Django logs for authentication errors
3. Verify token contents using [jwt.io](https://jwt.io)
4. Review Keycloak client configuration
