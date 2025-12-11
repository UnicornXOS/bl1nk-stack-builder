# =============================================================================
# bl1nk Agent Builder - Makefile
# =============================================================================
# Description: Development and deployment automation
# Author: MiniMax Agent
# Version: 1.0.0
# =============================================================================

.PHONY: help install dev prod test lint format clean docker build deploy

# Default target
help: ## Show this help message
	@echo "🚀 bl1nk Agent Builder - Development Commands"
	@echo "============================================"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "🔧 Quick Start:"
	@echo "  make install     - Install dependencies"
	@echo "  make dev         - Start development environment"
	@echo "  make test        - Run all tests"
	@echo "  make clean       - Clean up containers and data"

# =============================================================================
# Installation & Setup
# =============================================================================

install: ## Install all dependencies
	@echo "📦 Installing dependencies..."
	@./scripts/bootstrap.sh development
	@echo "✅ Dependencies installed successfully!"

dev-setup: ## Setup development environment
	@echo "🛠️  Setting up development environment..."
	@./scripts/setup_dependency.sh
	@./scripts/generate_api_keys.sh
	@./scripts/validate_secrets.sh
	@echo "✅ Development environment ready!"

# =============================================================================
# Development
# =============================================================================

dev: ## Start development environment with docker-compose
	@echo "🚀 Starting development environment..."
	@docker-compose up -d
	@echo "✅ Development environment started!"
	@echo ""
	@echo "🌐 Services available at:"
	@echo "  📊 API:        http://localhost:8000"
	@echo "  🔧 Admin:      http://localhost:3000"
	@echo "  📈 Grafana:    http://localhost:3001"
	@echo "  🗄️  pgAdmin:    http://localhost:5050"
	@echo "  📊 Prometheus: http://localhost:9090"

dev-stop: ## Stop development environment
	@echo "🛑 Stopping development environment..."
	@docker-compose down
	@echo "✅ Development environment stopped!"

dev-restart: dev-stop dev ## Restart development environment
	@echo "🔄 Development environment restarted!"

dev-logs: ## Show development logs
	@docker-compose logs -f

dev-shell-api: ## Open shell in API container
	@docker-compose exec api bash

dev-shell-worker: ## Open shell in Worker container
	@docker-compose exec worker bash

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	@echo "🧪 Running tests..."
	@./scripts/run_tests.sh

test-unit: ## Run unit tests only
	@echo "🧪 Running unit tests..."
	@docker-compose exec api pytest tests/unit -v

test-integration: ## Run integration tests only
	@echo "🧪 Running integration tests..."
	@docker-compose exec api pytest tests/integration -v

test-coverage: ## Run tests with coverage report
	@echo "🧪 Running tests with coverage..."
	@docker-compose exec api pytest --cov=app --cov-report=html --cov-report=term

test-load: ## Run load tests
	@echo "🧪 Running load tests..."
	@./scripts/load_test.sh

# =============================================================================
# Code Quality
# =============================================================================

format: ## Format code (Python & TypeScript)
	@echo "🎨 Formatting code..."
	@echo "  Formatting Python..."
	@docker-compose exec api black apps/worker/
	@docker-compose exec api isort apps/worker/
	@echo "  Formatting TypeScript..."
	@docker-compose exec worker npm run format
	@docker-compose exec admin npm run format
	@echo "✅ Code formatted!"

lint: ## Run linting
	@echo "🔍 Running linting..."
	@echo "  Python linting..."
	@docker-compose exec api ruff check apps/worker/
	@echo "  TypeScript linting..."
	@docker-compose exec worker npm run lint
	@docker-compose exec admin npm run lint
	@echo "✅ Linting completed!"

type-check: ## Run type checking
	@echo "🔍 Running type checking..."
	@docker-compose exec worker npm run type-check
	@docker-compose exec admin npm run type-check
	@echo "✅ Type checking completed!"

security-audit: ## Run security audit
	@echo "🔒 Running security audit..."
	@docker-compose exec api safety check
	@docker-compose exec api bandit -r apps/worker/
	@echo "✅ Security audit completed!"

# =============================================================================
# Database Management
# =============================================================================

db-migrate: ## Run database migrations
	@echo "🗄️  Running database migrations..."
	@docker-compose exec api python -m alembic upgrade head

db-reset: ## Reset database (WARNING: Deletes all data)
	@echo "⚠️  Resetting database..."
	@docker-compose exec postgres psql -U bl1nk -c "DROP DATABASE IF EXISTS bl1nk;"
	@docker-compose exec postgres psql -U bl1nk -c "CREATE DATABASE bl1nk;"
	@docker-compose exec api python -m alembic upgrade head
	@echo "✅ Database reset completed!"

db-backup: ## Backup database
	@echo "💾 Backing up database..."
	@mkdir -p backups
	@docker-compose exec postgres pg_dump -U bl1nk bl1nk > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backup completed!"

db-restore: ## Restore database from backup
	@read -p "Enter backup filename: " filename; \
	docker-compose exec postgres psql -U bl1nk -c "DROP DATABASE IF EXISTS bl1nk;"; \
	docker-compose exec postgres psql -U bl1nk -c "CREATE DATABASE bl1nk;"; \
	cat backups/$$filename | docker-compose exec -T postgres psql -U bl1nk bl1nk
	@echo "✅ Database restore completed!"

db-shell: ## Open database shell
	@docker-compose exec postgres psql -U bl1nk bl1nk

# =============================================================================
# Monitoring & Billing
# =============================================================================

billing-check: ## Check current billing status
	@echo "💰 Checking billing status..."
	@./scripts/billing_monitor.sh check

billing-monitor: ## Start billing monitoring
	@echo "📊 Starting billing monitor..."
	@./scripts/billing_monitor.sh daily

billing-report: ## Generate billing report
	@echo "📊 Generating billing report..."
	@./scripts/billing_monitor.sh report

billing-config: ## Setup billing configuration
	@echo "⚙️  Setting up billing configuration..."
	@./scripts/billing_monitor.sh config

monitoring: ## Check system monitoring
	@echo "📊 Checking system monitoring..."
	@curl -s http://localhost:8000/metrics | head -20
	@echo ""
	@echo "🌐 Grafana: http://localhost:3001 (admin/admin123)"
	@echo "📈 Prometheus: http://localhost:9090"

# =============================================================================
# Build & Deployment
# =============================================================================

build: ## Build Docker images
	@echo "🏗️  Building Docker images..."
	@docker-compose build --no-cache
	@echo "✅ Docker images built successfully!"

build-api: ## Build API image only
	@echo "🏗️  Building API image..."
	@docker build -f Dockerfile.api -t bl1nk-api:latest .

build-worker: ## Build Worker image only
	@echo "🏗️  Building Worker image..."
	@docker build -f Dockerfile.worker -t bl1nk-worker:latest .

build-admin: ## Build Admin image only
	@echo "🏗️  Building Admin image..."
	@docker build -f Dockerfile.admin -t bl1nk-admin:latest .

# =============================================================================
# Production
# =============================================================================

prod: ## Start production environment
	@echo "🚀 Starting production environment..."
	@docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "✅ Production environment started!"

prod-stop: ## Stop production environment
	@echo "🛑 Stopping production environment..."
	@docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
	@echo "✅ Production environment stopped!"

deploy: ## Deploy to production
	@echo "🚀 Deploying to production..."
	@./scripts/deploy.sh production
	@echo "✅ Deployment completed!"

deploy-staging: ## Deploy to staging
	@echo "🚀 Deploying to staging..."
	@./scripts/deploy.sh staging
	@echo "✅ Staging deployment completed!"

# =============================================================================
# Health Checks
# =============================================================================

health: ## Check system health
	@echo "🏥 Checking system health..."
	@echo "API Health:"
	@curl -s http://localhost:8000/health | jq . || echo "API not responding"
	@echo ""
	@echo "Database Health:"
	@docker-compose exec postgres pg_isready -U bl1nk
	@echo ""
	@echo "Redis Health:"
	@docker-compose exec redis redis-cli ping

status: ## Show service status
	@echo "📊 Service Status:"
	@docker-compose ps

# =============================================================================
# Utilities
# =============================================================================

clean: ## Clean up containers and images
	@echo "🧹 Cleaning up..."
	@docker-compose down -v --remove-orphans
	@docker system prune -f
	@echo "✅ Cleanup completed!"

clean-all: ## Clean up everything including volumes
	@echo "🧹 Deep cleaning..."
	@docker-compose down -v --remove-orphans --rmi all
	@docker system prune -af --volumes
	@echo "✅ Deep cleanup completed!"

logs: ## Show all service logs
	@docker-compose logs -f --tail=100

shell: ## Open bash shell in the project root
	@bash

project-stats: ## Show project statistics
	@./scripts/project_stats.sh

verify-setup: ## Verify project setup
	@./scripts/verify_structure.sh
	@./scripts/validate_secrets.sh

# =============================================================================
# Documentation
# =============================================================================

docs: ## Generate documentation
	@echo "📚 Generating documentation..."
	@./scripts/generate_docs.sh

docs-serve: ## Serve documentation locally
	@echo "📚 Starting documentation server..."
	@cd docs && python -m http.server 8080

# =============================================================================
# Git Operations
# =============================================================================

git-hooks: ## Install git hooks
	@echo "🪝 Installing git hooks..."
	@./scripts/setup_git_hooks.sh

commit: ## Commit with conventional commits format
	@if [ -z "$$1" ]; then echo "Usage: make commit TYPE=feat|fix|docs|..."; exit 1; fi
	@./scripts/conventional_commit.sh $(TYPE) "$(MSG)"

release: ## Create a new release
	@./scripts/create_release.sh $(VERSION)

# =============================================================================
# Development Scripts
# =============================================================================

demo: ## Run the demo suite
	@echo "🎮 Running demo suite..."
	@./scripts/demo.sh

demo-data: ## Generate sample data for RAG
	@echo "🎯 Generating sample data..."
	@./scripts/generate_sample_data.sh

test-providers: ## Test all AI providers
	@echo "🤖 Testing AI providers..."
	@./scripts/test_providers.sh

benchmark: ## Run performance benchmarks
	@echo "⚡ Running benchmarks..."
	@./scripts/benchmark.sh

# =============================================================================
# Environment Management
# =============================================================================

env-check: ## Check environment configuration
	@echo "🔍 Checking environment..."
	@./scripts/check_environment.sh

env-export: ## Export environment variables
	@echo "📤 Exporting environment variables..."
	@./scripts/export_env.sh

env-validate: ## Validate environment variables
	@echo "✅ Validating environment..."
	@./scripts/validate_secrets.sh

# =============================================================================
# Security
# =============================================================================

security-scan: ## Run security scans
	@echo "🔒 Running security scans..."
	@docker run --rm -v $(PWD):/src owasp/zap2docker-stable zap-baseline.py -t http://localhost:8000

ssl-setup: ## Setup SSL certificates
	@echo "🔒 Setting up SSL certificates..."
	@./scripts/setup_ssl.sh

# =============================================================================
# CI/CD
# =============================================================================

ci-test: ## Run CI tests
	@echo "🔄 Running CI tests..."
	@make test
	@make lint
	@make type-check
	@make security-audit

ci-build: ## Run CI build
	@echo "🔄 Running CI build..."
	@make build
	@make test-coverage

ci-deploy: ## Run CI deployment
	@echo "🔄 Running CI deployment..."
	@make deploy

# =============================================================================
# Development Workflow
# =============================================================================

# One-command development setup
quick-start: install dev-setup dev ## Complete development setup (alias for install dev-setup dev)

# Development workflow
develop: format lint test dev ## Complete development workflow

# Production deployment workflow
release-prep: clean test lint security-audit build ## Prepare for release

# Quick commands
up: dev ## Alias for dev
down: dev-stop ## Alias for dev-stop
restart: dev-restart ## Alias for dev-restart