#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Django application...${NC}"

# Wait for PostgreSQL to be ready
echo -e "${YELLOW}Waiting for PostgreSQL...${NC}"
while ! nc -z ${DB_HOST:-db} ${DB_PORT:-5432}; do
  sleep 0.1
done
echo -e "${GREEN}PostgreSQL started${NC}"

# Wait for Redis to be ready
echo -e "${YELLOW}Waiting for Redis...${NC}"
while ! nc -z ${REDIS_HOST:-redis} ${REDIS_PORT:-6379}; do
  sleep 0.1
done
echo -e "${GREEN}Redis started${NC}"

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
python manage.py migrate --noinput
echo -e "${GREEN}Migrations completed${NC}"

# Collect static files (only in production)
if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.prod" ]; then
    echo -e "${YELLOW}Collecting static files...${NC}"
    python manage.py collectstatic --noinput
    echo -e "${GREEN}Static files collected${NC}"
fi

# Create superuser if credentials are provided
if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo -e "${YELLOW}Creating superuser...${NC}"
    python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='$DJANGO_SUPERUSER_EMAIL').exists():
    User.objects.create_superuser(
        email='$DJANGO_SUPERUSER_EMAIL',
        password='$DJANGO_SUPERUSER_PASSWORD',
        first_name='${DJANGO_SUPERUSER_FIRST_NAME:-Admin}',
        last_name='${DJANGO_SUPERUSER_LAST_NAME:-User}'
    )
    print('Superuser created successfully')
else:
    print('Superuser already exists')
END
    echo -e "${GREEN}Superuser check completed${NC}"
fi

echo -e "${GREEN}Starting application server...${NC}"

# Execute the main command
exec "$@"
