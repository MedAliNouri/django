# Keycloak Integration - Quick Start

This guide gets you up and running with Keycloak SSO in 5 minutes.

## TL;DR - The Flow

```bash
# 1. User registers in Keycloak (not Django)
# 2. User logs in to Keycloak → gets token
# 3. User calls Django API with token
# 4. Django middleware auto-creates user from token
# 5. Everything just works! ✨
```

## Prerequisites

1. **Keycloak server running** (e.g., `http://localhost:8080`)
2. **Keycloak client configured** (see setup below)
3. **User created in Keycloak** with username and password

## Quick Setup (5 steps)

### Step 1: Configure Keycloak Server

Create a client in Keycloak Admin Console:

1. Go to `http://localhost:8080/admin`
2. Select your realm (or create new one)
3. Navigate to **Clients** → **Create Client**
4. Set:
   - Client ID: `django-client`
   - Client Protocol: `openid-connect`
   - Access Type: `confidential`
   - Direct Access Grants: `Enabled`
   - Valid Redirect URIs: `*` (for dev)
   - Web Origins: `*` (for dev)
5. Go to **Credentials** tab → Copy the **Secret**

### Step 2: Update Django Configuration

Edit `.env` file:

```bash
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=django-client
KEYCLOAK_CLIENT_SECRET=paste-secret-here
```

### Step 3: Rebuild Django Container

```bash
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.dev.yml build
docker compose -f docker-compose.dev.yml up
```

### Step 4: Create Test User in Keycloak

In Keycloak Admin Console:

1. Go to **Users** → **Add User**
2. Set:
   - Username: `testuser`
   - Email: `test@example.com`
   - First Name: `Test`
   - Last Name: `User`
3. Go to **Credentials** tab
4. Set password: `password123` (disable temporary)

### Step 5: Test the Integration

#### Option A: Using the Test Script

```bash
./test_keycloak_flow.sh
```

#### Option B: Manual Testing

```bash
# 1. Get token from Keycloak
curl -X POST http://localhost:8080/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=django-client" \
  -d "client_secret=YOUR_SECRET" \
  -d "grant_type=password" \
  -d "username=testuser" \
  -d "password=password123" | jq -r '.access_token'

# Save the token
export TOKEN="paste-token-here"

# 2. Call Django API (user will be auto-created!)
curl -X GET http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Bearer $TOKEN"
```

#### Option C: Using Postman

1. Import `postman_collection.json`
2. Run: **Keycloak Authentication → Keycloak Login**
   - Update username/password
3. Run: **User Management → Get Current User (Me)**
   - Token automatically included
   - User auto-created in Django!

## How It Works

### The Magic: Middleware Auto-Sync

```
Request with Keycloak token
         ↓
Django Middleware intercepts
         ↓
Validates token with Keycloak
         ↓
Extracts user info from token
         ↓
Creates/updates Django user
         ↓
Attaches user to request
         ↓
Your view receives authenticated user
```

### Zero Configuration Required

The middleware (`KeycloakAuthenticationMiddleware`) is already configured and will:

✅ Automatically validate Keycloak tokens
✅ Create Django users on first login
✅ Update user info on subsequent logins
✅ Work alongside existing Django JWT auth

### No Separate Registration

Users **do not register in Django**. They register in Keycloak, and Django syncs automatically.

## Testing Checklist

- [ ] Keycloak server accessible
- [ ] Client created and secret copied
- [ ] `.env` updated with Keycloak config
- [ ] Django container rebuilt
- [ ] Test user created in Keycloak
- [ ] Token obtained from Keycloak
- [ ] `/me` endpoint returns user data
- [ ] User visible in Django admin

## Common Issues

### 1. "Invalid token"

**Check:**
- Token not expired (tokens expire in 5-15 min)
- Keycloak server URL is correct in `.env`
- Client secret is correct

**Solution:**
```bash
# Get fresh token
curl -X POST http://localhost:8080/realms/master/protocol/openid-connect/token ...
```

### 2. "Connection refused"

**Check:**
- Keycloak server is running
- URL is accessible from Django container

**Solution:**
```bash
# If Keycloak on host machine, use:
KEYCLOAK_SERVER_URL=http://host.docker.internal:8080
```

### 3. User not created in Django

**Check:**
- Middleware enabled in settings (already done)
- Token contains email claim
- Django logs for errors

**Solution:**
```bash
# Check logs
docker compose -f docker-compose.dev.yml logs -f web | grep -i keycloak
```

### 4. "Invalid client credentials"

**Check:**
- Client ID matches exactly
- Client secret is correct
- Client type is "confidential"

**Solution:**
- Regenerate secret in Keycloak
- Update `.env` and rebuild

## Verify Everything Works

```bash
# 1. Get token
TOKEN=$(curl -s -X POST http://localhost:8080/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=django-client" \
  -d "client_secret=YOUR_SECRET" \
  -d "grant_type=password" \
  -d "username=testuser" \
  -d "password=password123" | jq -r '.access_token')

# 2. Test Django API
curl -X GET http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# 3. Check user in Django
docker compose -f docker-compose.dev.yml exec web python manage.py shell
>>> from apps.users.models import User
>>> User.objects.filter(email='test@example.com').exists()
True
```

## Architecture

```
┌─────────────────┐
│   Keycloak      │  ← Users register & login here
│   (Port 8080)   │
└────────┬────────┘
         │ Issues JWT token
         ↓
┌─────────────────┐
│   Frontend      │  ← Stores token, sends with requests
│   Application   │
└────────┬────────┘
         │ Authorization: Bearer <token>
         ↓
┌─────────────────┐
│ Django Middleware│ ← Validates & auto-creates users
│   (Port 8000)   │
└────────┬────────┘
         │ request.user = authenticated_user
         ↓
┌─────────────────┐
│  Django Views   │  ← Receives authenticated user
│  & Database     │
└─────────────────┘
```

## What's Next?

1. **Frontend Integration:** Use Keycloak JavaScript adapter
2. **Production Setup:** Configure proper URLs and SSL
3. **Role Mapping:** Map Keycloak roles to Django permissions
4. **User Management:** Manage users in Keycloak Admin Console

## Documentation

- **Complete Guide:** [`docs/KEYCLOAK_INTEGRATION.md`](docs/KEYCLOAK_INTEGRATION.md)
- **Simple Flow:** [`docs/KEYCLOAK_SIMPLE_FLOW.md`](docs/KEYCLOAK_SIMPLE_FLOW.md)
- **Postman Guide:** [`docs/POSTMAN_GUIDE.md`](docs/POSTMAN_GUIDE.md)
- **Test Script:** [`test_keycloak_flow.sh`](test_keycloak_flow.sh)

## Support

Need help? Check:

1. Keycloak server logs
2. Django logs: `docker compose logs -f web`
3. Token contents at [jwt.io](https://jwt.io)
4. Keycloak documentation: [keycloak.org](https://www.keycloak.org/docs)

---

**That's it!** Users register in Keycloak, Django syncs automatically. Simple! 🚀
