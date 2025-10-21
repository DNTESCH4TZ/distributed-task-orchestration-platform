.PHONY: help install dev-install update clean test test-cov lint format type-check security pre-commit run run-worker migrate migrate-create docker-up docker-down docs

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ========================================
# Installation & Dependencies
# ========================================

install:  ## Install production dependencies
	poetry install --no-dev

dev-install:  ## Install all dependencies (including dev)
	poetry install
	poetry run pre-commit install

update:  ## Update dependencies
	poetry update
	poetry export -f requirements.txt --output requirements.txt --without-hashes

clean:  ## Clean up cache and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -f .coverage

# ========================================
# Testing
# ========================================

test:  ## Run tests
	poetry run pytest tests/ -v

test-unit:  ## Run unit tests only
	poetry run pytest tests/unit/ -v

test-integration:  ## Run integration tests only
	poetry run pytest tests/integration/ -v

test-e2e:  ## Run e2e tests only
	poetry run pytest tests/e2e/ -v

test-cov:  ## Run tests with coverage report
	poetry run pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

test-watch:  ## Run tests in watch mode
	poetry run ptw tests/

# ========================================
# Code Quality
# ========================================

lint:  ## Run linters (flake8, pylint)
	poetry run flake8 src/ tests/
	poetry run pylint src/

format:  ## Format code with black and isort
	poetry run black src/ tests/
	poetry run isort src/ tests/

format-check:  ## Check if code is formatted
	poetry run black --check src/ tests/
	poetry run isort --check-only src/ tests/

type-check:  ## Run type checking with mypy
	poetry run mypy src/

security:  ## Run security checks
	poetry run bandit -r src/
	poetry run safety check

pre-commit:  ## Run pre-commit hooks on all files
	poetry run pre-commit run --all-files

# ========================================
# Application
# ========================================

run:  ## Run application with uvicorn (development)
	poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

run-prod:  ## Run application with optimized settings (production)
	poetry run uvicorn src.main:app \
		--host 0.0.0.0 \
		--port 8000 \
		--workers 4 \
		--loop uvloop \
		--http httptools \
		--backlog 2048 \
		--no-access-log

run-worker:  ## Run Celery worker
	poetry run celery -A src.infrastructure.messaging.celery.app worker --loglevel=info

run-beat:  ## Run Celery beat scheduler
	poetry run celery -A src.infrastructure.messaging.celery.app beat --loglevel=info

# ========================================
# Database
# ========================================

migrate:  ## Run database migrations
	poetry run alembic upgrade head

migrate-rollback:  ## Rollback last migration
	poetry run alembic downgrade -1

migrate-create:  ## Create new migration (usage: make migrate-create msg="your message")
	poetry run alembic revision --autogenerate -m "$(msg)"

migrate-history:  ## Show migration history
	poetry run alembic history

db-seed:  ## Seed database with test data
	poetry run python scripts/seed_data.py

# ========================================
# Docker
# ========================================

docker-build:  ## Build Docker image
	docker build -t task-orchestrator:latest -f deploy/docker/Dockerfile .

docker-up:  ## Start all services with docker-compose
	docker-compose -f deploy/docker/docker-compose.yml up -d

docker-down:  ## Stop all services
	docker-compose -f deploy/docker/docker-compose.yml down

docker-logs:  ## Show docker-compose logs
	docker-compose -f deploy/docker/docker-compose.yml logs -f

docker-ps:  ## Show running containers
	docker-compose -f deploy/docker/docker-compose.yml ps

docker-restart:  ## Restart services
	docker-compose -f deploy/docker/docker-compose.yml restart

# ========================================
# Monitoring & Health
# ========================================

health:  ## Check application health
	poetry run python scripts/health_check.py

metrics:  ## Open Prometheus metrics endpoint
	@echo "Opening http://localhost:8000/metrics"
	@python -m webbrowser http://localhost:8000/metrics

grafana:  ## Open Grafana dashboard
	@echo "Opening http://localhost:3000"
	@python -m webbrowser http://localhost:3000

prometheus:  ## Open Prometheus UI
	@echo "Opening http://localhost:9090"
	@python -m webbrowser http://localhost:9090

jaeger:  ## Open Jaeger tracing UI
	@echo "Opening http://localhost:16686"
	@python -m webbrowser http://localhost:16686

# ========================================
# Documentation
# ========================================

docs:  ## Build documentation
	cd docs && poetry run mkdocs build

docs-serve:  ## Serve documentation locally
	cd docs && poetry run mkdocs serve

api-docs:  ## Open OpenAPI docs
	@echo "Opening http://localhost:8000/docs"
	@python -m webbrowser http://localhost:8000/docs

# ========================================
# Performance
# ========================================

profile:  ## Profile application with py-spy
	poetry run py-spy top -- python -m uvicorn src.main:app

load-test:  ## Run load tests (requires locust)
	locust -f tests/performance/locustfile.py

# ========================================
# All-in-one commands
# ========================================

setup:  ## Complete setup (install deps, setup pre-commit, run migrations)
	make dev-install
	make migrate
	@echo "✅ Setup complete! Run 'make run' to start the application."

check:  ## Run all checks (format, lint, type-check, security, tests)
	make format-check
	make lint
	make type-check
	make security
	make test

ci:  ## Run CI pipeline locally
	make format-check
	make lint
	make type-check
	make security
	make test-cov

