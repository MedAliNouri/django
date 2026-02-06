# Keycloak Simple Authentication Flow

This guide shows the simplified Keycloak authentication flow where users register in Keycloak and Django automatically creates user accounts on first login.

## Overview

```
┌──────────────┐
│   Keycloak   │  1. User registers here
│    Server    │  2. User logs in here
└──────┬───────┘
       │ 3. Returns token
       ↓
┌──────────────┐
│   Frontend   │  4. Stores token
│  (or Client) │  5. Sends token with requests
└──────┬───────┘
       │ 6. Authorization: Bearer <token>
       ↓
┌──────────────┐
│    Django    │  7. Middleware validates token
│   Middleware │  8. Auto-creates/updates user
│              │  9. Attaches user to request
└──────┬───────┘
       │ 10. Request processed
       ↓
┌──────────────┐
│   API View   │  11. request.user available
│              │  12. Returns response
└──────────────┘
```

## Step-by-Step Flow

### Step 1: Register User in Keycloak

Users register directly in Keycloak (not through Django).

**Option A: Keycloak Admin Console**
1. Go to Keycloak Admin Console
2. Select your realm
3. Navigate to Users → Add User
4. Fill in user details (username, email, first name, last name)
5. Go to Credentials tab → Set Password

**Option B: Keycloak User Registration (if enabled)**
1. Go to your Keycloak realm login page
2. Click "Register"
3. Fill in the registration form
4. Verify email if required

### Step 2: Get Token from Keycloak

**Option A: Direct Token Request (for testing)**

```bash
curl -X POST http://localhost:8080/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=django-client" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "grant_type=password" \
  -d "username=testuser" \
  -d "password=password123"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 300,
  "refresh_expires_in": 1800,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer"
}
```

**Option B: Via Django API (convenience endpoint)**

```bash
curl -X POST http://localhost:8000/api/v1/auth/keycloak/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

**Option C: OAuth2 Authorization Code Flow (production)**

This is handled by your frontend application using Keycloak's JavaScript adapter or any OAuth2 library.

### Step 3: Make Request to Django API

Now use the Keycloak token to access Django API. The middleware will automatically create the user in Django database.

```bash
# Call /me endpoint - User will be auto-created in Django
curl -X GET http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Bearer YOUR_KEYCLOAK_ACCESS_TOKEN"
```

**What happens behind the scenes:**

1. ✅ Middleware intercepts the request
2. ✅ Validates token with Keycloak (using JWKS)
3. ✅ Extracts user info from token (email, name, etc.)
4. ✅ Creates Django user if doesn't exist
5. ✅ Updates user info if already exists
6. ✅ Attaches user to `request.user`
7. ✅ View returns user data

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "testuser@example.com",
  "first_name": "Test",
  "last_name": "User",
  "full_name": "Test User",
  "is_active": true,
  "is_verified": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Step 4: Make Any Authenticated Request

All authenticated endpoints now work with the Keycloak token:

```bash
# List users
curl -X GET http://localhost:8000/api/v1/users/ \
  -H "Authorization: Bearer YOUR_KEYCLOAK_ACCESS_TOKEN"

# Update profile
curl -X PATCH http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Bearer YOUR_KEYCLOAK_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Updated",
    "bio": "My new bio"
  }'
```

## Configuration

### Django Settings (already configured)

```python
# config/settings/base.py

MIDDLEWARE = [
    # ...
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.users.middleware.KeycloakAuthenticationMiddleware',  # Auto-sync
    # ...
]

# Keycloak configuration
KEYCLOAK_SERVER_URL = 'http://localhost:8080'
KEYCLOAK_REALM = 'master'
KEYCLOAK_CLIENT_ID = 'django-client'
KEYCLOAK_CLIENT_SECRET = 'your-client-secret'
```

### Environment Variables

Update your `.env` file:

```bash
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=your-realm-name
KEYCLOAK_CLIENT_ID=django-client
KEYCLOAK_CLIENT_SECRET=your-client-secret-from-keycloak
```

### Keycloak Client Setup

1. **Create Client in Keycloak:**
   - Client ID: `django-client`
   - Client Protocol: `openid-connect`
   - Access Type: `confidential`
   - Valid Redirect URIs: `*` (for development) or specific URLs
   - Web Origins: `*` (for development) or specific URLs

2. **Enable Password Grant (for testing):**
   - Direct Access Grants Enabled: `ON`

3. **Get Client Secret:**
   - Go to Credentials tab
   - Copy the Secret value
   - Add to `.env` file

## How Middleware Works

The `KeycloakAuthenticationMiddleware` automatically:

### 1. Token Detection
```python
# Looks for Authorization header
Authorization: Bearer <keycloak_token>
```

### 2. Token Validation
- Validates signature using Keycloak's public keys (JWKS)
- Checks token expiration
- Verifies audience and issuer

### 3. User Synchronization
- Extracts user data from token claims:
  - `email` → Django user email
  - `given_name` → first_name
  - `family_name` → last_name
  - `email_verified` → is_verified

### 4. User Creation/Update
```python
# If user doesn't exist
user = User.objects.create(
    email=token['email'],
    first_name=token['given_name'],
    last_name=token['family_name'],
    is_active=True,
    is_verified=token['email_verified']
)

# If user exists, update fields
user.first_name = token['given_name']
user.last_name = token['family_name']
user.save()
```

### 5. Request Attachment
```python
# User is attached to request
request.user = user
request.keycloak_token = token
request.keycloak_payload = payload
```

## Testing the Flow

### 1. Create Keycloak User

```bash
# Via Keycloak Admin Console or CLI
# Username: john.doe
# Email: john.doe@example.com
# Password: SecurePass123!
```

### 2. Get Token

```bash
# Direct from Keycloak
TOKEN=$(curl -s -X POST http://localhost:8080/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=django-client" \
  -d "client_secret=YOUR_SECRET" \
  -d "grant_type=password" \
  -d "username=john.doe" \
  -d "password=SecurePass123!" | jq -r '.access_token')

echo "Token: $TOKEN"
```

### 3. Test Django API

```bash
# First request - User will be auto-created
curl -X GET http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Bearer $TOKEN"

# Check Django admin - user should now exist
# http://localhost:8000/admin/users/user/
```

### 4. Check Django Database

```bash
# Connect to database
docker compose -f docker-compose.dev.yml exec db psql -U django_user -d django_db

# Query users
SELECT id, email, first_name, last_name, is_active, created_at
FROM users
WHERE email = 'john.doe@example.com';
```

## Advantages of This Flow

### ✅ Simple Integration
- No separate user registration in Django
- Users managed centrally in Keycloak
- Django users created automatically

### ✅ Single Source of Truth
- Keycloak is the authoritative user directory
- Django syncs user data from Keycloak tokens
- User updates in Keycloak propagate to Django

### ✅ Seamless SSO
- Users login once in Keycloak
- Same token works across all services
- No password management in Django

### ✅ Security
- Tokens validated using public key cryptography
- No password storage in Django
- Centralized token revocation

## Token Lifecycle

### Access Token (Short-lived)
- Expires in 5-15 minutes (configurable in Keycloak)
- Used for API requests
- Validated on every request

### Refresh Token (Long-lived)
- Expires in 30 minutes to 1 day (configurable)
- Used to get new access tokens
- Should be stored securely by client

### Refresh Flow

```bash
# When access token expires, refresh it
curl -X POST http://localhost:8080/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=django-client" \
  -d "client_secret=YOUR_SECRET" \
  -d "grant_type=refresh_token" \
  -d "refresh_token=YOUR_REFRESH_TOKEN"
```

Or use Django convenience endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/auth/keycloak/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

## Troubleshooting

### User Not Created

**Problem:** Request succeeds but user not in Django database

**Check:**
1. Middleware is enabled in settings
2. Token is valid and not expired
3. Token contains email claim
4. Check Django logs for errors

```bash
docker compose -f docker-compose.dev.yml logs -f web | grep -i keycloak
```

### Token Validation Failed

**Problem:** 401 Unauthorized or "Invalid token"

**Solutions:**
1. Verify Keycloak server URL is correct
2. Check token is not expired (decode at jwt.io)
3. Ensure Keycloak is accessible from Django
4. Verify client credentials in `.env`

### User Already Exists

**Problem:** "User with email X already exists"

**This is normal!** The middleware handles this:
- Finds existing user
- Updates user info from token
- Returns user data

### CORS Issues

**Problem:** CORS errors when calling from frontend

**Solution:**
```python
# config/settings/base.py
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:8080',
    'https://your-frontend-domain.com',
]
```

## Frontend Integration Example

### JavaScript (React/Vue/Angular)

```javascript
// 1. Login via Keycloak (using keycloak-js library)
import Keycloak from 'keycloak-js';

const keycloak = new Keycloak({
  url: 'http://localhost:8080',
  realm: 'master',
  clientId: 'django-client'
});

await keycloak.init({ onLoad: 'login-required' });

// 2. Get token
const token = keycloak.token;

// 3. Call Django API
const response = await fetch('http://localhost:8000/api/v1/users/me/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const user = await response.json();
console.log('Django user:', user);
```

## Summary

This simplified flow:
1. ✅ Users register in Keycloak
2. ✅ Users login via Keycloak (get token)
3. ✅ Frontend/client includes token in requests
4. ✅ Django middleware auto-creates users
5. ✅ No separate registration needed in Django
6. ✅ Single source of truth (Keycloak)

The middleware handles everything automatically - you just need to send valid Keycloak tokens with your requests!
