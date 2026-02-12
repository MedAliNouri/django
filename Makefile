.PHONY: help build up down restart logs shell test lint format migrate makemigrations superuser clean validate

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# Docker commands
build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker-compose -f docker-compose.dev.yml build

up: ## Start development environment
	@echo "$(BLUE)Starting development environment...$(NC)"
	docker-compose -f docker-compose.dev.yml up -d
	@echo "$(GREEN)✓ Development environment started$(NC)"
	@echo "$(YELLOW)API: http://localhost:8000$(NC)"
	@echo "$(YELLOW)Admin: http://localhost:8000/admin$(NC)"
	@echo "$(YELLOW)API Docs: http://localhost:8000/api/docs$(NC)"

down: ## Stop development environment
	@echo "$(BLUE)Stopping development environment...$(NC)"
	docker-compose -f docker-compose.dev.yml down
	@echo "$(GREEN)✓ Development environment stopped$(NC)"

restart: down up ## Restart development environment

logs: ## Show logs
	docker-compose -f docker-compose.dev.yml logs -f

logs-web: ## Show web container logs
	docker-compose -f docker-compose.dev.yml logs -f web

shell: ## Open Django shell
	docker-compose -f docker-compose.dev.yml exec web python manage.py shell

bash: ## Open bash shell in web container
	docker-compose -f docker-compose.dev.yml exec web bash

# Database commands
migrate: ## Run database migrations
	@echo "$(BLUE)Running migrations...$(NC)"
	docker-compose -f docker-compose.dev.yml exec web python manage.py migrate
	@echo "$(GREEN)✓ Migrations completed$(NC)"

makemigrations: ## Create new migrations
	@echo "$(BLUE)Creating migrations...$(NC)"
	docker-compose -f docker-compose.dev.yml exec web python manage.py makemigrations
	@echo "$(GREEN)✓ Migrations created$(NC)"

superuser: ## Create superuser
	docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser

dbshell: ## Open database shell
	docker-compose -f docker-compose.dev.yml exec db psql -U django_user -d django_db

# Testing commands
test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	docker-compose -f docker-compose.dev.yml exec web pytest
	@echo "$(GREEN)✓ Tests completed$(NC)"

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	docker-compose -f docker-compose.dev.yml exec web pytest --cov --cov-report=html
	@echo "$(GREEN)✓ Coverage report generated at htmlcov/index.html$(NC)"

test-fast: ## Run tests in parallel
	@echo "$(BLUE)Running tests in parallel...$(NC)"
	docker-compose -f docker-compose.dev.yml exec web pytest -n auto
	@echo "$(GREEN)✓ Tests completed$(NC)"

test-unit: ## Run only unit tests
	docker-compose -f docker-compose.dev.yml exec web pytest -m unit

test-integration: ## Run only integration tests
	docker-compose -f docker-compose.dev.yml exec web pytest -m integration

# Code quality commands
lint: ## Run linters
	@echo "$(BLUE)Running linters...$(NC)"
	docker-compose -f docker-compose.dev.yml exec web ruff check .
	@echo "$(GREEN)✓ Linting completed$(NC)"

lint-fix: ## Run linters with auto-fix
	@echo "$(BLUE)Running linters with auto-fix...$(NC)"
	docker-compose -f docker-compose.dev.yml exec web ruff check --fix .
	@echo "$(GREEN)✓ Linting completed$(NC)"

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	docker-compose -f docker-compose.dev.yml exec web ruff format .
	@echo "$(GREEN)✓ Code formatted$(NC)"

type-check: ## Run type checking
	@echo "$(BLUE)Running type checking...$(NC)"
	docker-compose -f docker-compose.dev.yml exec web mypy .
	@echo "$(GREEN)✓ Type checking completed$(NC)"

format-check: ## Check code formatting without making changes
	@echo "$(BLUE)Checking code formatting...$(NC)"
	docker-compose -f docker-compose.dev.yml exec web ruff format --check apps config tests
	@echo "$(GREEN)✓ Format check completed$(NC)"

validate: ## Run complete validation suite (format check, lint, type-check, test)
	@echo "$(BLUE)Running validation suite...$(NC)"
	@echo "$(YELLOW)1/4 Checking code formatting...$(NC)"
	@docker-compose -f docker-compose.dev.yml run --rm --no-deps -e RUFF_NO_CACHE=1 web ruff format --check apps config tests || (echo "$(RED)✗ Format check failed$(NC)" && exit 1)
	@echo "$(GREEN)✓ Format check passed$(NC)"
	@echo "$(YELLOW)2/4 Running linters...$(NC)"
	@docker-compose -f docker-compose.dev.yml run --rm --no-deps -e RUFF_NO_CACHE=1 web ruff check apps config tests || (echo "$(RED)✗ Linting failed$(NC)" && exit 1)
	@echo "$(GREEN)✓ Linting passed$(NC)"
	@echo "$(YELLOW)3/4 Running type checking...$(NC)"
	@docker-compose -f docker-compose.dev.yml run --rm --no-deps web mypy apps config || (echo "$(RED)✗ Type checking failed$(NC)" && exit 1)
	@echo "$(GREEN)✓ Type checking passed$(NC)"
	@echo "$(YELLOW)4/4 Running tests...$(NC)"
	@docker-compose -f docker-compose.dev.yml run --rm web pytest || (echo "$(RED)✗ Tests failed$(NC)" && exit 1)
	@echo "$(GREEN)✓ Tests passed$(NC)"
	@echo "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo "$(GREEN)✓ All validation checks passed!$(NC)"
	@echo "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"

check: lint type-check test ## Run all checks (lint, type-check, test)

# Production commands
build-prod: ## Build production Docker images
	@echo "$(BLUE)Building production images...$(NC)"
	docker-compose -f docker-compose.prod.yml build

up-prod: ## Start production environment
	@echo "$(BLUE)Starting production environment...$(NC)"
	docker-compose -f docker-compose.prod.yml up -d
	@echo "$(GREEN)✓ Production environment started$(NC)"

down-prod: ## Stop production environment
	docker-compose -f docker-compose.prod.yml down

logs-prod: ## Show production logs
	docker-compose -f docker-compose.prod.yml logs -f

# Utility commands
clean: ## Clean up temporary files
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup completed$(NC)"

collectstatic: ## Collect static files
	docker-compose -f docker-compose.dev.yml exec web python manage.py collectstatic --noinput

dump-data: ## Dump database data
	docker-compose -f docker-compose.dev.yml exec web python manage.py dumpdata --indent 2 > data.json

load-data: ## Load database data
	docker-compose -f docker-compose.dev.yml exec web python manage.py loaddata data.json

backup-db: ## Backup database
	@echo "$(BLUE)Backing up database...$(NC)"
	docker-compose -f docker-compose.dev.yml exec db pg_dump -U django_user django_db > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✓ Database backed up$(NC)"

# Pre-commit hooks
pre-commit-install: ## Install pre-commit hooks
	pre-commit install

pre-commit-run: ## Run pre-commit hooks on all files
	pre-commit run --all-files

# Docker cleanup
prune: ## Remove unused Docker resources
	@echo "$(YELLOW)Removing unused Docker resources...$(NC)"
	docker system prune -af --volumes
	@echo "$(GREEN)✓ Docker cleanup completed$(NC)"
