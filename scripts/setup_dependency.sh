#!/bin/bash
# =============================================================================
# bl1nk-agent-builder Dependency Setup Script
# =============================================================================
# 
# This script sets up all dependencies required for bl1nk-agent-builder
# including Docker, Docker Compose, and all project dependencies.
#
# Usage:
#   ./scripts/setup_dependency.sh [environment]
#
# Arguments:
#   environment - Environment to setup (development, staging, production)
#                 Defaults to 'development'
#
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-development}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
DOCKER_COMPOSE_ENV_FILE="$PROJECT_ROOT/.env.docker"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed"
        return 1
    fi
    return 0
}

# =============================================================================
# System Requirements Check
# =============================================================================

check_system_requirements() {
    log_info "Checking system requirements..."
    
    # Check OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        log_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
    
    log_success "Operating system: $OS"
    
    # Check architecture
    ARCH=$(uname -m)
    log_info "Architecture: $ARCH"
    
    # Check available disk space (minimum 10GB)
    AVAILABLE_SPACE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [[ $AVAILABLE_SPACE -lt 10 ]]; then
        log_error "Insufficient disk space. Required: 10GB, Available: ${AVAILABLE_SPACE}GB"
        exit 1
    fi
    
    log_success "Sufficient disk space available"
}

# =============================================================================
# Docker Installation
# =============================================================================

install_docker() {
    log_info "Setting up Docker..."
    
    if check_command "docker"; then
        log_success "Docker is already installed"
        docker --version
    else
        log_info "Installing Docker..."
        
        if [[ "$OS" == "linux" ]]; then
            # Ubuntu/Debian
            if command -v apt &> /dev/null; then
                sudo apt update
                sudo apt install -y docker.io docker-compose-plugin
                sudo usermod -aG docker $USER
                log_success "Docker installed successfully"
                log_warning "Please log out and back in for group changes to take effect"
            # CentOS/RHEL/Fedora
            elif command -v yum &> /dev/null; then
                sudo yum install -y docker docker-compose
                sudo systemctl start docker
                sudo systemctl enable docker
                sudo usermod -aG docker $USER
                log_success "Docker installed successfully"
            else
                log_error "Unsupported Linux distribution"
                exit 1
            fi
        elif [[ "$OS" == "macos" ]]; then
            log_error "Please install Docker Desktop for Mac from: https://www.docker.com/products/docker-desktop"
            exit 1
        fi
    fi
    
    # Check Docker Compose
    if check_command "docker compose"; then
        log_success "Docker Compose is available"
        docker compose version
    else
        log_error "Docker Compose is not available. Please install Docker Desktop."
        exit 1
    fi
}

# =============================================================================
# Python Environment Setup
# =============================================================================

setup_python_environment() {
    log_info "Setting up Python environment..."
    
    # Check Python version
    if check_command "python3"; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_info "Python version: $PYTHON_VERSION"
        
        # Check if version is 3.9+
        if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
            log_error "Python 3.9+ is required. Current version: $PYTHON_VERSION"
            exit 1
        fi
    else
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    # Setup virtual environment
    if [[ ! -d "$PROJECT_ROOT/.venv" ]]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv "$PROJECT_ROOT/.venv"
        log_success "Virtual environment created"
    else
        log_success "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source "$PROJECT_ROOT/.venv/bin/activate"
    
    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip
    
    # Install pip-tools
    log_info "Installing pip-tools..."
    pip install pip-tools
    
    # Install dependencies
    if [[ -f "$PROJECT_ROOT/apps/worker/requirements.in" ]]; then
        log_info "Compiling Python dependencies..."
        pip-compile apps/worker/requirements.in --output-file apps/worker/requirements.txt
        
        log_info "Installing Python dependencies..."
        pip install -r apps/worker/requirements.txt --no-deps
        pip check
        
        log_success "Python dependencies installed"
    else
        log_warning "requirements.in not found, skipping Python dependency installation"
    fi
}

# =============================================================================
# Node.js and pnpm Setup
# =============================================================================

setup_nodejs_environment() {
    log_info "Setting up Node.js environment..."
    
    # Check Node.js version
    if check_command "node"; then
        NODE_VERSION=$(node --version)
        log_info "Node.js version: $NODE_VERSION"
    else
        log_error "Node.js is not installed. Please install Node.js 18+ from: https://nodejs.org/"
        exit 1
    fi
    
    # Install pnpm if not available
    if check_command "pnpm"; then
        log_success "pnpm is already installed"
        pnpm --version
    else
        log_info "Installing pnpm..."
        npm install -g pnpm
        log_success "pnpm installed"
    fi
    
    # Install project dependencies
    log_info "Installing Node.js dependencies..."
    
    # Bridge app dependencies
    if [[ -f "$PROJECT_ROOT/apps/bridge/package.json" ]]; then
        log_info "Installing bridge app dependencies..."
        pnpm install --prefix apps/bridge
    fi
    
    # UI app dependencies (if exists)
    if [[ -f "$PROJECT_ROOT/ui/nextjs/package.json" ]]; then
        log_info "Installing UI app dependencies..."
        pnpm install --prefix ui/nextjs
    fi
    
    log_success "Node.js dependencies installed"
}

# =============================================================================
# Database Setup
# =============================================================================

setup_database() {
    log_info "Setting up database..."
    
    # Create database directory
    mkdir -p "$PROJECT_ROOT/data/postgres"
    mkdir -p "$PROJECT_ROOT/data/redis"
    
    # Create database initialization script
    cat > "$PROJECT_ROOT/init-db.sql" << 'EOF'
-- Initialize bl1nk-agent-builder database
CREATE DATABASE bl1nk;
CREATE USER bl1nk_user WITH ENCRYPTED PASSWORD 'bl1nk_password';
GRANT ALL PRIVILEGES ON DATABASE bl1nk TO bl1nk_user;
\c bl1nk;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
EOF
    
    log_success "Database setup files created"
}

# =============================================================================
# Environment Configuration
# =============================================================================

setup_environment() {
    log_info "Setting up environment configuration..."
    
    # Copy environment template
    if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
        if [[ -f "$PROJECT_ROOT/config/env.example" ]]; then
            cp "$PROJECT_ROOT/config/env.example" "$PROJECT_ROOT/.env"
            log_success "Environment file created from template"
            log_warning "Please edit .env with your actual configuration values"
        else
            log_warning "env.example not found, creating basic .env file"
            cat > "$PROJECT_ROOT/.env" << EOF
# bl1nk-agent-builder Environment Configuration
ENVIRONMENT=$ENVIRONMENT

# Database
DB_DSN=postgresql://bl1nk_user:bl1nk_password@localhost:5432/bl1nk

# Redis
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET_KEY=your_jwt_secret_key_here_change_in_production
ADMIN_API_KEY=your_admin_api_key_here

# Providers
OPENROUTER_API_KEY=your_openrouter_api_key
CLOUDFLARE_API_TOKEN=your_cloudflare_token
BEDROCK_ACCESS_KEY_ID=your_bedrock_access_key
BEDROCK_SECRET_ACCESS_KEY=your_bedrock_secret_key

# Object Storage
R2_ACCOUNT_ID=your_r2_account_id
R2_ACCESS_KEY=your_r2_access_key
R2_SECRET_KEY=your_r2_secret_key

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
SENTRY_DSN=your_sentry_dsn

# Logging
LOG_LEVEL=INFO
EOF
        fi
    else
        log_success "Environment file already exists"
    fi
    
    # Create Docker environment file
    cat > "$DOCKER_COMPOSE_ENV_FILE" << EOF
# Docker Compose Environment
COMPOSE_PROJECT_NAME=bl1nk-agent-builder
ENVIRONMENT=$ENVIRONMENT

# Database
POSTGRES_DB=bl1nk
POSTGRES_USER=bl1nk_user
POSTGRES_PASSWORD=bl1nk_password

# Redis
REDIS_PASSWORD=bl1nk_redis_password

# Services
FASTAPI_PORT=8000
WORKER_PORT=8001
UI_PORT=3000
EOF
    
    log_success "Environment configuration completed"
}

# =============================================================================
# Docker Compose Configuration
# =============================================================================

create_docker_compose() {
    log_info "Creating Docker Compose configuration..."
    
    cat > "$DOCKER_COMPOSE_FILE" << 'EOF'
version: '3.8'

services:
  # PostgreSQL Database with pgvector
  postgres:
    image: ankane/pgvector:latest
    container_name: bl1nk-postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-bl1nk}
      POSTGRES_USER: ${POSTGRES_USER:-bl1nk_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-bl1nk_password}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/migrations:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-bl1nk_user}"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - bl1nk-network

  # Redis for caching and queue
  redis:
    image: redis:7-alpine
    container_name: bl1nk-redis
    environment:
      REDIS_PASSWORD: ${REDIS_PASSWORD:-bl1nk_redis_password}
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --requirepass ${REDIS_PASSWORD:-bl1nk_redis_password}
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - bl1nk-network

  # FastAPI Worker
  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    container_name: bl1nk-worker
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER:-bl1nk_user}:${POSTGRES_PASSWORD:-bl1nk_password}@postgres:5432/${POSTGRES_DB:-bl1nk}
      - REDIS_URL=redis://:${REDIS_PASSWORD:-bl1nk_redis_password}@redis:6379
      - ENVIRONMENT=${ENVIRONMENT:-development}
    env_file:
      - .env
    ports:
      - "${FASTAPI_PORT:-8000}:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - bl1nk-network
    restart: unless-stopped

  # Cloudflare Worker (Edge Layer)
  bridge:
    build:
      context: ./apps/bridge
      dockerfile: Dockerfile
    container_name: bl1nk-bridge
    environment:
      - WORKER_URL=http://worker:8000
      - ENVIRONMENT=${ENVIRONMENT:-development}
    ports:
      - "${BRIDGE_PORT:-8787}:8787"
    depends_on:
      worker:
        condition: service_healthy
    networks:
      - bl1nk-network
    restart: unless-stopped

  # Next.js UI (Optional)
  ui:
    build:
      context: ./ui/nextjs
      dockerfile: Dockerfile
    container_name: bl1nk-ui
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:${FASTAPI_PORT:-8000}
      - NEXT_PUBLIC_WORKER_URL=http://localhost:${BRIDGE_PORT:-8787}
    ports:
      - "${UI_PORT:-3000}:3000"
    depends_on:
      - worker
      - bridge
    networks:
      - bl1nk-network
    restart: unless-stopped

  # Monitoring - Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: bl1nk-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./infra/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    networks:
      - bl1nk-network
    restart: unless-stopped

  # Monitoring - Grafana
  grafana:
    image: grafana/grafana:latest
    container_name: bl1nk-grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana_data:/var/lib/grafana
      - ./infra/grafana/provisioning:/etc/grafana/provisioning
    depends_on:
      - prometheus
    networks:
      - bl1nk-network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  bl1nk-network:
    driver: bridge
EOF
    
    log_success "Docker Compose configuration created"
}

# =============================================================================
# Docker Files Creation
# =============================================================================

create_docker_files() {
    log_info "Creating Docker files..."
    
    # Worker Dockerfile
    cat > "$PROJECT_ROOT/Dockerfile.worker" << 'EOF'
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY apps/worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY apps/worker/ .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
EOF
    
    # Bridge Dockerfile
    mkdir -p "$PROJECT_ROOT/apps/bridge"
    cat > "$PROJECT_ROOT/apps/bridge/Dockerfile" << 'EOF'
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY src/ ./src/

# Expose port
EXPOSE 8787

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8787/health || exit 1

# Run worker
CMD ["npm", "start"]
EOF
    
    # UI Dockerfile (Next.js)
    mkdir -p "$PROJECT_ROOT/ui/nextjs"
    cat > "$PROJECT_ROOT/ui/nextjs/Dockerfile" << 'EOF'
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build application
RUN npm run build

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

# Start application
CMD ["npm", "start"]
EOF
    
    log_success "Docker files created"
}

# =============================================================================
# Database Migration Setup
# =============================================================================

setup_migrations() {
    log_info "Setting up database migrations..."
    
    # Ensure migrations directory exists
    mkdir -p "$PROJECT_ROOT/sql/migrations"
    
    # Create migration runner script
    cat > "$PROJECT_ROOT/scripts/run_migrations.sh" << 'EOF'
#!/bin/bash
# Run database migrations

set -e

DATABASE_URL=${DATABASE_URL:-"postgresql://bl1nk_user:bl1nk_password@localhost:5432/bl1nk"}

echo "Running database migrations..."

# Run migrations in order
for migration in sql/migrations/*.sql; do
    if [[ -f "$migration" ]]; then
        echo "Running migration: $(basename "$migration")"
        psql "$DATABASE_URL" -f "$migration"
    fi
done

echo "Database migrations completed successfully"
EOF
    
    chmod +x "$PROJECT_ROOT/scripts/run_migrations.sh"
    
    log_success "Migration setup completed"
}

# =============================================================================
# Development Tools Setup
# =============================================================================

setup_development_tools() {
    log_info "Setting up development tools..."
    
    # Create development scripts
    mkdir -p "$PROJECT_ROOT/scripts"
    
    # Development start script
    cat > "$PROJECT_ROOT/scripts/dev.sh" << 'EOF'
#!/bin/bash
# Start development environment

set -e

echo "Starting bl1nk-agent-builder development environment..."

# Activate virtual environment
source .venv/bin/activate

# Run database migrations
./scripts/run_migrations.sh

# Start services
docker compose -f docker-compose.yml up --build -d

echo "Development environment started!"
echo ""
echo "Services:"
echo "  - FastAPI Worker: http://localhost:8000"
echo "  - Cloudflare Worker: http://localhost:8787"  
echo "  - UI: http://localhost:3000"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3001 (admin/admin123)"
echo ""
echo "To view logs: docker compose logs -f"
echo "To stop: docker compose down"
EOF
    
    chmod +x "$PROJECT_ROOT/scripts/dev.sh"
    
    # Production start script
    cat > "$PROJECT_ROOT/scripts/start.sh" << 'EOF'
#!/bin/bash
# Start production environment

set -e

echo "Starting bl1nk-agent-builder production environment..."

# Run database migrations
./scripts/run_migrations.sh

# Start services
docker compose -f docker-compose.yml up --build -d

echo "Production environment started!"
echo ""
echo "Services are running in detached mode"
echo "To view logs: docker compose logs -f"
echo "To stop: docker compose down"
EOF
    
    chmod +x "$PROJECT_ROOT/scripts/start.sh"
    
    # Health check script
    cat > "$PROJECT_ROOT/scripts/health_check.sh" << 'EOF'
#!/bin/bash
# Check system health

echo "Checking bl1nk-agent-builder health..."

# Check Docker services
echo "Checking Docker services..."
docker compose ps

# Check API health
echo "Checking API health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ FastAPI Worker: Healthy"
else
    echo "❌ FastAPI Worker: Unhealthy"
fi

# Check Worker bridge
echo "Checking Worker bridge..."
if curl -f http://localhost:8787/health > /dev/null 2>&1; then
    echo "✅ Cloudflare Worker: Healthy"
else
    echo "❌ Cloudflare Worker: Unhealthy"
fi

echo "Health check completed"
EOF
    
    chmod +x "$PROJECT_ROOT/scripts/health_check.sh"
    
    log_success "Development tools setup completed"
}

# =============================================================================
# Final Setup and Validation
# =============================================================================

final_validation() {
    log_info "Running final validation..."
    
    # Check if all services can start
    log_info "Testing service startup..."
    
    if docker compose config > /dev/null 2>&1; then
        log_success "Docker Compose configuration is valid"
    else
        log_error "Docker Compose configuration is invalid"
        exit 1
    fi
    
    # Check file permissions
    if [[ -x "$PROJECT_ROOT/scripts/dev.sh" ]]; then
        log_success "Script permissions are correct"
    else
        log_error "Script permissions need to be fixed"
        exit 1
    fi
    
    # Check environment file
    if [[ -f "$PROJECT_ROOT/.env" ]]; then
        log_success "Environment file exists"
    else
        log_warning "Environment file not found"
    fi
    
    log_success "Final validation completed"
}

# =============================================================================
# Cleanup Function
# =============================================================================

cleanup_on_error() {
    log_error "Setup failed. Cleaning up..."
    # Add cleanup logic here if needed
    exit 1
}

# Set up error handling
trap cleanup_on_error ERR

# =============================================================================
# Main Execution
# =============================================================================

main() {
    log_info "Starting bl1nk-agent-builder dependency setup..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Project root: $PROJECT_ROOT"
    
    # Check if running as script directory
    if [[ ! -f "$SCRIPT_DIR/setup_dependency.sh" ]]; then
        log_error "Please run this script from the project root directory"
        exit 1
    fi
    
    # Run setup steps
    check_system_requirements
    install_docker
    setup_python_environment
    setup_nodejs_environment
    setup_database
    setup_environment
    create_docker_compose
    create_docker_files
    setup_migrations
    setup_development_tools
    final_validation
    
    log_success "Setup completed successfully!"
    echo ""
    echo "🎉 bl1nk-agent-builder is ready to use!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Edit .env file with your configuration"
    echo "   2. Run: ./scripts/dev.sh (development) or ./scripts/start.sh (production)"
    echo "   3. Access services at:"
    echo "      - API: http://localhost:8000"
    echo "      - Worker: http://localhost:8787"
    echo "      - UI: http://localhost:3000"
    echo "      - Prometheus: http://localhost:9090"
    echo "      - Grafana: http://localhost:3001"
    echo ""
    echo "🔧 Useful commands:"
    echo "   - View logs: docker compose logs -f"
    echo "   - Health check: ./scripts/health_check.sh"
    echo "   - Stop services: docker compose down"
    echo "   - Run migrations: ./scripts/run_migrations.sh"
    echo ""
    log_info "Happy coding! 🚀"
}

# Run main function
main "$@"