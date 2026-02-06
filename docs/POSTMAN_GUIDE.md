# Postman Collection Guide

This guide explains how to import and use the Postman collection to test the Django REST Framework API with Keycloak integration.

## Import Collection

### Method 1: Import from File
1. Open Postman
2. Click **Import** button (top left)
3. Select **File** tab
4. Choose `postman_collection.json` from the project root
5. Click **Import**

### Method 2: Import via URL (if using Git)
1. Copy the raw URL of `postman_collection.json` from your repository
2. In Postman, click **Import**
3. Select **Link** tab
4. Paste the URL
5. Click **Continue** and then **Import**

## Collection Structure

The collection is organized into the following folders:

### 1. Health Check
- **Health Check** - Verify API is running

### 2. Django JWT Authentication
- **Register User** - Create new user account
- **Login (Get JWT Token)** - Authenticate and get tokens
- **Refresh JWT Token** - Refresh expired access token
- **Verify JWT Token** - Verify token validity

### 3. Keycloak Authentication
- **Get Keycloak Config** - Get Keycloak server configuration
- **Keycloak Login** - Login with Keycloak credentials
- **Keycloak Refresh Token** - Refresh Keycloak access token
- **Keycloak Get User Info** - Get user info from Keycloak
- **Keycloak Logout** - Invalidate refresh token

### 4. User Management
- **Get Current User (Me)** - Get authenticated user profile
- **Update Current User** - Update user profile
- **List All Users** - List all users with pagination
- **Get User by ID** - Get specific user details
- **Update User Profile** - Update profile information
- **Change Password** - Change user password
- **Get User Statistics** - Get user stats (admin only)

### 5. API Documentation
- **Get OpenAPI Schema** - Get API schema
- **Swagger UI** - Link to Swagger documentation

## Environment Variables

The collection uses the following variables (automatically managed):

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `base_url` | API base URL | `http://localhost:8000` |
| `access_token` | Django JWT access token | Auto-populated on login |
| `refresh_token` | Django JWT refresh token | Auto-populated on login |
| `keycloak_access_token` | Keycloak access token | Auto-populated on Keycloak login |
| `keycloak_refresh_token` | Keycloak refresh token | Auto-populated on Keycloak login |
| `user_id` | Created user ID | Auto-populated on registration |

### Updating Base URL

If your API runs on a different URL/port:

1. Click on the collection name
2. Go to **Variables** tab
3. Update `base_url` value (e.g., `http://localhost:3000` or `https://api.example.com`)
4. Click **Save**

## Testing Workflow

### Option 1: Django JWT Authentication

1. **Register a User**
   - Run `Django JWT Authentication → Register User`
   - Update email/password in request body if needed
   - User ID automatically saved to `{{user_id}}`

2. **Login**
   - Run `Django JWT Authentication → Login (Get JWT Token)`
   - Use same email/password from registration
   - Tokens automatically saved to `{{access_token}}` and `{{refresh_token}}`

3. **Test Authenticated Endpoints**
   - Run any request in **User Management** folder
   - Token is automatically included in Authorization header

4. **Refresh Token (when expired)**
   - Run `Django JWT Authentication → Refresh JWT Token`
   - New access token automatically saved

### Option 2: Keycloak Authentication

**Prerequisites:** Keycloak server must be configured (see `docs/KEYCLOAK_INTEGRATION.md`)

1. **Check Keycloak Configuration**
   - Run `Keycloak Authentication → Get Keycloak Config`
   - Verify server URL and realm are correct

2. **Keycloak Login**
   - Run `Keycloak Authentication → Keycloak Login`
   - Update username/password with your Keycloak credentials
   - Tokens automatically saved to `{{keycloak_access_token}}` and `{{keycloak_refresh_token}}`

3. **Test with Keycloak Token**
   - Run `Keycloak Authentication → Keycloak Get User Info`
   - Or use any authenticated endpoint with Keycloak token

4. **Refresh Keycloak Token**
   - Run `Keycloak Authentication → Keycloak Refresh Token`
   - New tokens automatically saved

5. **Logout**
   - Run `Keycloak Authentication → Keycloak Logout`
   - Invalidates refresh token

## Automatic Token Management

The collection includes **Tests** scripts that automatically:

1. **Extract tokens** from login responses
2. **Save tokens** to collection variables
3. **Include tokens** in subsequent requests
4. **Update tokens** after refresh

You don't need to manually copy/paste tokens between requests!

## Request Examples

### 1. Register User (Django)

```http
POST http://localhost:8000/api/v1/users/
Content-Type: application/json

{
  "email": "john.doe@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890"
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "phone_number": "+1234567890",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 2. Login (Django JWT)

```http
POST http://localhost:8000/api/v1/auth/login/
Content-Type: application/json

{
  "email": "john.doe@example.com",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 3. Keycloak Login

```http
POST http://localhost:8000/api/v1/auth/keycloak/login/
Content-Type: application/json

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

### 4. Get Current User

```http
GET http://localhost:8000/api/v1/users/me/
Authorization: Bearer {{access_token}}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "phone_number": "+1234567890",
  "is_active": true,
  "is_verified": false,
  "profile": {
    "company": "Tech Corp",
    "job_title": "Software Engineer",
    "location": "San Francisco, CA"
  },
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Query Parameters

### Pagination

All list endpoints support pagination:

```
GET /api/v1/users/?page=1&page_size=20
```

### Filtering

Filter users by various fields:

```
GET /api/v1/users/?is_active=true&is_verified=true
```

### Searching

Search across multiple fields:

```
GET /api/v1/users/?search=john
```

### Ordering

Order results by field:

```
GET /api/v1/users/?ordering=-created_at
```

Multiple orderings:
```
GET /api/v1/users/?ordering=last_name,first_name
```

## Common HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 204 | No Content | Resource deleted successfully |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Authentication required or failed |
| 403 | Forbidden | Permission denied |
| 404 | Not Found | Resource not found |
| 500 | Server Error | Internal server error |

## Troubleshooting

### "Unauthorized" Error (401)

**Problem:** Getting 401 on authenticated endpoints

**Solutions:**
1. Check if you've logged in first
2. Verify token is saved (check Variables tab)
3. Token might be expired - try refreshing
4. Re-run login request

### "Forbidden" Error (403)

**Problem:** Getting 403 on admin-only endpoints

**Solutions:**
1. Login with admin account
2. Check user has staff/superuser permissions
3. Some endpoints require specific permissions

### Keycloak Connection Error

**Problem:** "Failed to connect to Keycloak"

**Solutions:**
1. Verify Keycloak server is running
2. Check `KEYCLOAK_SERVER_URL` in Django settings
3. Ensure Keycloak is accessible from Django container
4. Update client credentials in `.env` file

### Token Expired

**Problem:** "Token has expired"

**Solutions:**
1. Run the refresh token request
2. Or login again to get new tokens

### CORS Error (in browser)

**Problem:** CORS policy blocking requests

**Solutions:**
1. This shouldn't affect Postman
2. If testing from browser, update `CORS_ALLOWED_ORIGINS` in Django settings
3. Postman automatically handles CORS

## Advanced Features

### Pre-request Scripts

The collection can be extended with pre-request scripts:

```javascript
// Example: Add timestamp to request
pm.environment.set("timestamp", new Date().toISOString());
```

### Test Scripts

Add custom test scripts to validate responses:

```javascript
// Verify response status
pm.test("Status is 200", function() {
    pm.response.to.have.status(200);
});

// Verify response structure
pm.test("Response has user object", function() {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('user');
});
```

### Running Collection

Run all requests in sequence:

1. Click on collection name
2. Click **Run** button
3. Select requests to run
4. Click **Run Django REST Framework API**

## Environment Setup (Optional)

For multiple environments (dev, staging, prod):

1. Click **Environments** (left sidebar)
2. Click **+** to create new environment
3. Add variables:
   ```
   base_url: http://localhost:8000  (or production URL)
   ```
4. Select environment from dropdown (top right)

## Export Modified Collection

After making changes:

1. Click on collection (three dots)
2. Click **Export**
3. Choose **Collection v2.1**
4. Save file

## Additional Resources

- [Postman Documentation](https://learning.postman.com/docs/)
- [API Documentation](http://localhost:8000/api/docs/)
- [Keycloak Integration Guide](./KEYCLOAK_INTEGRATION.md)
- [Django REST Framework Docs](https://www.django-rest-framework.org/)

## Support

For issues:
1. Check API logs: `docker compose -f docker-compose.dev.yml logs -f web`
2. Verify environment variables in `.env`
3. Review API documentation at `/api/docs/`
4. Check Keycloak server logs if using SSO
