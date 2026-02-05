# API Documentation

## Overview

This API follows REST principles and returns JSON responses wrapped in a consistent envelope format.

## Base URL

- Development: `http://localhost:8000/api`
- Production: `https://yourdomain.com/api`

## API Versioning

The API uses URL-based versioning:
- v1: `/api/v1/`
- v2: `/api/v2/`

## Response Format

All API responses follow a consistent envelope format:

### Success Response

```json
{
  "success": true,
  "data": {
    // Response data here
  },
  "meta": {
    // Metadata (e.g., pagination)
  }
}
```

### Error Response

```json
{
  "success": false,
  "data": null,
  "errors": {
    "code": "error_code",
    "message": "Human-readable error message",
    "details": {
      // Field-specific errors
    }
  },
  "meta": {}
}
```

### Paginated Response

```json
{
  "success": true,
  "data": [
    // Array of results
  ],
  "meta": {
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_count": 100,
      "total_pages": 5,
      "has_next": true,
      "has_previous": false,
      "next": "http://localhost:8000/api/v1/users/?page=2",
      "previous": null
    }
  }
}
```

## Authentication

The API uses JWT (JSON Web Token) authentication.

### Obtaining Tokens

**Request:**
```http
POST /api/v1/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Using Tokens

Include the access token in the Authorization header:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Refreshing Tokens

**Request:**
```http
POST /api/v1/auth/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Anonymous users**: 10 requests/minute (burst), 100 requests/hour (sustained)
- **Authenticated users**: 30 requests/minute (burst), 1000 requests/hour (sustained)

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 29
X-RateLimit-Reset: 1640000000
```

## Filtering and Searching

### Filtering

Use query parameters to filter results:

```http
GET /api/v1/users/?is_active=true&is_verified=true
```

### Searching

Use the `search` parameter:

```http
GET /api/v1/users/?search=john
```

### Ordering

Use the `ordering` parameter:

```http
GET /api/v1/users/?ordering=-created_at
```

Use `-` prefix for descending order.

### Pagination

Control pagination with query parameters:

```http
GET /api/v1/users/?page=2&page_size=50
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `validation_error` | 400 | Request validation failed |
| `authentication_failed` | 401 | Authentication credentials invalid |
| `permission_denied` | 403 | Insufficient permissions |
| `not_found` | 404 | Resource not found |
| `resource_conflict` | 409 | Resource conflict (e.g., duplicate) |
| `internal_server_error` | 500 | Internal server error |
| `service_unavailable` | 503 | Service temporarily unavailable |

## User Endpoints

### Register User

Create a new user account.

**Request:**
```http
POST /api/v1/users/
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "newuser@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "is_active": true,
    "is_verified": false,
    "created_at": "2024-01-01T00:00:00.000Z"
  },
  "meta": {}
}
```

### List Users

Get paginated list of users.

**Request:**
```http
GET /api/v1/users/
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "John Doe",
      "is_active": true,
      "is_verified": true,
      "avatar": null,
      "created_at": "2024-01-01T00:00:00.000Z"
    }
  ],
  "meta": {
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_count": 50,
      "total_pages": 3
    }
  }
}
```

### Get Current User

Get authenticated user's information.

**Request:**
```http
GET /api/v1/users/me/
Authorization: Bearer <token>
```

**Response:** `200 OK`

### Update User

Update user information.

**Request:**
```http
PATCH /api/v1/users/{id}/
Authorization: Bearer <token>
Content-Type: application/json

{
  "first_name": "Jane",
  "bio": "Software developer"
}
```

**Response:** `200 OK`

### Change Password

Change user password.

**Request:**
```http
POST /api/v1/users/me/change-password/
Authorization: Bearer <token>
Content-Type: application/json

{
  "old_password": "OldPass123!",
  "new_password": "NewPass456!",
  "new_password_confirm": "NewPass456!"
}
```

**Response:** `200 OK`

### User Statistics

Get aggregate user statistics.

**Request:**
```http
GET /api/v1/users/stats/
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "total": 150,
    "active": 140,
    "verified": 120,
    "staff": 5,
    "inactive": 10,
    "unverified": 30
  },
  "meta": {}
}
```

## Interactive Documentation

For interactive API documentation with the ability to test endpoints:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## SDKs and Client Libraries

Currently, no official SDKs are available. However, the OpenAPI schema can be used to generate clients in various languages:

```bash
# Download OpenAPI schema
curl http://localhost:8000/api/schema/ > openapi.json

# Generate client (example using openapi-generator)
openapi-generator generate -i openapi.json -g python -o ./client
```

## Webhooks

Webhooks are not currently supported but may be added in future versions.

## Best Practices

1. **Always use HTTPS in production**
2. **Store tokens securely** (e.g., in httpOnly cookies, not localStorage)
3. **Implement proper error handling** for all API calls
4. **Respect rate limits** to avoid being throttled
5. **Use pagination** for list endpoints
6. **Include correlation IDs** for debugging (via X-Correlation-ID header)

## Support

For API support or questions:
- GitHub Issues: [repository-url]/issues
- Email: api-support@example.com
