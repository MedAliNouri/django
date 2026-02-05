# Django REST Framework API

A production-grade Django REST Framework project with modern architecture, comprehensive testing, and complete Docker setup.

## Features

- **Modern Architecture**: Service layer, selector pattern, and repository pattern for clean separation of concerns
- **Authentication**: JWT-based authentication with refresh tokens and blacklisting
- **API Versioning**: URL-based versioning (v1, v2)
- **Docker**: Complete Docker setup for development and production
- **Testing**: Comprehensive test suite with pytest
- **Code Quality**: Ruff, mypy, and pre-commit hooks
- **API Documentation**: Auto-generated OpenAPI 3.0 documentation with Swagger UI
- **Async Tasks**: Celery for background job processing
- **Caching**: Redis-based caching layer
- **Monitoring**: Health check endpoints and structured logging
- **Security**: Production-ready security settings

## Architecture

### Design Patterns

1. **Service Layer Pattern**: All business logic in `services.py`
2. **Selector Pattern**: All read operations in `selectors.py`
3. **Repository Pattern**: Data access abstraction in `repositories.py`
4. **Command Query Separation**: Reads through selectors, writes through services

### Project Structure

```
project_root/
├── apps/
│   ├── core/           # Base classes, utilities, middleware
│   ├── users/          # User domain (example)
│   └── common/         # Shared behaviors and types
├── config/             # Django settings and configuration
├── docker/             # Docker configuration files
├── requirements/       # Python dependencies
├── tests/              # Global test fixtures
└── docs/              # Documentation
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Make (optional, for convenience commands)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd django
   ```

2. **Copy environment file**
   ```bash
   cp .env.example .env
   ```

3. **Build and start services**
   ```bash
   make build
   make up
   ```

   Or without Make:
   ```bash
   docker-compose -f docker-compose.dev.yml build
   docker-compose -f docker-compose.dev.yml up -d
   ```

4. **Access the application**
   - API: http://localhost:8000
   - Admin: http://localhost:8000/admin
   - API Docs: http://localhost:8000/api/docs
   - Mailpit (email testing): http://localhost:8025
   - Flower (Celery monitoring): http://localhost:5555

### Initial Setup

Create a superuser:
```bash
make superuser
```

Or:
```bash
docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

## Development

### Common Commands

```bash
# Start development environment
make up

# View logs
make logs

# Run tests
make test

# Run tests with coverage
make test-cov

# Run linters
make lint

# Format code
make format

# Run type checking
make type-check

# Access Django shell
make shell

# Create migrations
make makemigrations

# Run migrations
make migrate

# Stop environment
make down
```

### Running Tests

```bash
# All tests
make test

# With coverage
make test-cov

# Specific test file
docker-compose -f docker-compose.dev.yml exec web pytest apps/users/tests/test_api.py

# Unit tests only
make test-unit

# Integration tests only
make test-integration
```

### Code Quality

```bash
# Run all checks
make check

# Lint only
make lint

# Auto-fix linting issues
make lint-fix

# Format code
make format

# Type checking
make type-check
```

## API Documentation

### API Endpoints

#### Authentication
- `POST /api/v1/auth/login/` - Obtain JWT token
- `POST /api/v1/auth/refresh/` - Refresh JWT token
- `POST /api/v1/auth/verify/` - Verify JWT token

#### Users
- `GET /api/v1/users/` - List users
- `POST /api/v1/users/` - Create user (register)
- `GET /api/v1/users/{id}/` - Get user details
- `PATCH /api/v1/users/{id}/` - Update user
- `DELETE /api/v1/users/{id}/` - Delete user
- `GET /api/v1/users/me/` - Get current user
- `PATCH /api/v1/users/me/profile/` - Update current user profile
- `POST /api/v1/users/me/change-password/` - Change password
- `GET /api/v1/users/stats/` - Get user statistics

### Interactive API Documentation

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI Schema**: http://localhost:8000/api/schema

## Architecture Decisions

### Service Layer Pattern

All business logic lives in services. Services are responsible for:
- Data validation beyond what serializers provide
- Complex business rules
- Orchestrating multiple operations
- Calling external services

Example:
```python
# In services.py
class UserService:
    @staticmethod
    def create_user(email: str, password: str, **kwargs) -> User:
        # Business logic here
        if user_exists(email):
            raise ResourceConflictError("Email already exists")

        user = UserRepository.create(email=email, password=password, **kwargs)
        UserProfileRepository.create(user=user)
        send_welcome_email.delay(user.id)
        return user
```

### Selector Pattern

All read operations go through selectors. Selectors are pure functions that:
- Return querysets or data
- Handle filtering and searching
- Optimize database queries

Example:
```python
# In selectors.py
def get_user_list(is_active: bool = None, search: str = None) -> QuerySet:
    queryset = UserRepository.get_all()

    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)

    if search:
        queryset = queryset.filter(email__icontains=search)

    return queryset.select_related('profile')
```

### Repository Pattern

Repositories abstract database operations:
- Provide clean interface for data access
- Hide ORM implementation details
- Make testing easier

Example:
```python
# In repositories.py
class UserRepository:
    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        try:
            return User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return None

    @staticmethod
    def create(email: str, password: str, **kwargs) -> User:
        return User.objects.create_user(email=email, password=password, **kwargs)
```

## Production Deployment

### Environment Variables

Copy `.env.example` to `.env` and set production values:

```bash
DJANGO_SETTINGS_MODULE=config.settings.prod
DEBUG=False
SECRET_KEY=<strong-secret-key>
ALLOWED_HOSTS=yourdomain.com
DB_NAME=production_db
DB_USER=prod_user
DB_PASSWORD=<strong-password>
DB_SSL_REQUIRE=True
SENTRY_DSN=<your-sentry-dsn>
```

### Production Deployment

```bash
# Build production images
make build-prod

# Start production services
make up-prod

# View production logs
make logs-prod
```

### Security Checklist

- [ ] Set strong `SECRET_KEY`
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Enable database SSL (`DB_SSL_REQUIRE=True`)
- [ ] Configure CORS for your frontend domain
- [ ] Set up Sentry for error tracking
- [ ] Configure email for production
- [ ] Review and update security middleware settings
- [ ] Set up SSL/TLS certificates (Let's Encrypt recommended)
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Enable logging and monitoring

## Testing Strategy

### Test Structure

- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test API endpoints and database interactions
- **Fixtures**: Reusable test data in `conftest.py`
- **Factories**: Factory Boy for generating test data

### Test Coverage

Run tests with coverage:
```bash
make test-cov
```

Coverage report will be available at `htmlcov/index.html`

## Contributing

### Pre-commit Hooks

Install pre-commit hooks:
```bash
make pre-commit-install
```

Hooks will run automatically on commit:
- Trailing whitespace removal
- YAML/JSON validation
- Ruff linting and formatting
- MyPy type checking
- Secret detection

### Code Style

- Follow PEP 8 (enforced by Ruff)
- Use type hints where appropriate
- Write docstrings for public functions/classes
- Keep functions small and focused
- Maximum line length: 120 characters

## Monitoring and Logging

### Health Check

```bash
curl http://localhost:8000/health/
```

Response:
```json
{
  "status": "healthy",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "Database connection successful"
    },
    "cache": {
      "status": "healthy",
      "message": "Cache connection successful"
    }
  }
}
```

### Logs

View logs:
```bash
# All services
make logs

# Specific service
make logs-web
make logs-celery
```

### Celery Monitoring

Access Flower at http://localhost:5555 for Celery task monitoring.

## Troubleshooting

### Common Issues

**Database connection errors**
```bash
# Check database is running
docker-compose -f docker-compose.dev.yml ps db

# View database logs
docker-compose -f docker-compose.dev.yml logs db
```

**Migration errors**
```bash
# Reset database (development only!)
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d
```

**Port already in use**
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

## License

[Your License Here]

## Contact

[Your Contact Information]
