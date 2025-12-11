#!/bin/bash
set -e

# =============================================================================
# bl1nk-agent-builder Bootstrap Script
# =============================================================================
# This script sets up the entire development environment for bl1nk-agent-builder
# It creates the project structure, installs dependencies, and configures the environment
#
# Usage: ./scripts/bootstrap.sh [environment]
# Environments: development, staging, production
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT=${1:-development}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        missing_tools+=("python3")
    else
        python_version=$(python3 --version | cut -d' ' -f2)
        log_info "Found Python $python_version"
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        missing_tools+=("node")
    else
        node_version=$(node --version)
        log_info "Found Node.js $node_version"
    fi
    
    # Check pnpm
    if ! command -v pnpm &> /dev/null; then
        log_warning "pnpm not found. Installing globally..."
        npm install -g pnpm
    else
        pnpm_version=$(pnpm --version)
        log_info "Found pnpm $pnpm_version"
    fi
    
    # Check PostgreSQL client
    if ! command -v psql &> /dev/null; then
        log_warning "psql not found. Please install PostgreSQL client."
        missing_tools+=("psql")
    else
        log_info "Found PostgreSQL client"
    fi
    
    # Check pip-tools
    if ! python3 -c "import piptools" 2>/dev/null; then
        log_warning "pip-tools not found. Will install later."
    else
        log_info "Found pip-tools"
    fi
    
    # Check wrangler (for Cloudflare Workers)
    if ! command -v wrangler &> /dev/null; then
        log_warning "wrangler not found. Installing globally..."
        npm install -g wrangler
    else
        wrangler_version=$(wrangler --version)
        log_info "Found wrangler $wrangler_version"
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_error "Missing tools: ${missing_tools[*]}"
        log_error "Please install missing tools and run this script again."
        exit 1
    fi
    
    log_success "All prerequisites satisfied"
}

# Create project structure
create_project_structure() {
    log_info "Creating project structure..."
    
    cd "$PROJECT_ROOT"
    
    # Create all necessary directories
    local directories=(
        "apps/bridge/src"
        "apps/worker/app/routes"
        "apps/worker/app/services"
        "apps/worker/app/models"
        "apps/worker/app/utils"
        "packages/schema"
        "sql/migrations"
        "config"
        "docs"
        "scripts"
        "ui/nextjs"
        "tests/unit"
        "tests/integration"
        "tests/fixtures"
        ".github/workflows"
        "infra/terraform"
        "infra/prometheus"
        "infra/grafana"
        "logs"
        "data"
        "temp"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        log_info "Created directory: $dir"
    done
    
    # Create placeholder files for important directories
    touch apps/bridge/src/.gitkeep
    touch apps/worker/app/routes/.gitkeep
    touch apps/worker/app/services/.gitkeep
    touch apps/worker/app/models/.gitkeep
    touch apps/worker/app/utils/.gitkeep
    touch packages/schema/.gitkeep
    touch sql/migrations/.gitkeep
    touch config/.gitkeep
    touch docs/.gitkeep
    touch scripts/.gitkeep
    touch ui/nextjs/.gitkeep
    touch tests/unit/.gitkeep
    touch tests/integration/.gitkeep
    touch tests/fixtures/.gitkeep
    touch .github/workflows/.gitkeep
    touch infra/terraform/.gitkeep
    touch infra/prometheus/.gitkeep
    touch infra/grafana/.gitkeep
    touch logs/.gitkeep
    touch data/.gitkeep
    touch temp/.gitkeep
    
    log_success "Project structure created"
}

# Setup Python environment
setup_python_environment() {
    log_info "Setting up Python environment..."
    
    cd "$PROJECT_ROOT"
    
    # Create virtual environment
    if [ ! -d ".venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install pip-tools
    log_info "Installing pip-tools..."
    pip install pip-tools
    
    # Compile requirements
    log_info "Compiling Python requirements..."
    if [ -f "apps/worker/requirements.in" ]; then
        pip-compile apps/worker/requirements.in --output-file apps/worker/requirements.txt
    fi
    
    # Install dependencies
    if [ -f "apps/worker/requirements.txt" ]; then
        log_info "Installing Python dependencies..."
        pip install -r apps/worker/requirements.txt --no-deps
        pip check
    fi
    
    # Install additional development dependencies
    log_info "Installing development dependencies..."
    pip install \
        pytest-asyncio \
        httpx \
        python-dotenv \
        black \
        isort \
        ruff \
        mypy \
        pre-commit
    
    log_success "Python environment setup complete"
}

# Setup Node.js environment
setup_nodejs_environment() {
    log_info "Setting up Node.js environment..."
    
    cd "$PROJECT_ROOT"
    
    # Setup bridge app
    if [ -f "apps/bridge/package.json" ]; then
        log_info "Installing bridge dependencies..."
        pnpm install --prefix apps/bridge
    fi
    
    # Setup Next.js UI
    if [ -f "ui/nextjs/package.json" ]; then
        log_info "Installing UI dependencies..."
        pnpm install --prefix ui/nextjs
    fi
    
    # Install global development tools
    log_info "Installing global development tools..."
    npm install -g @typescript-eslint/eslint-plugin \
                   @typescript-eslint/parser \
                   eslint \
                   prettier \
                   typescript
    
    log_success "Node.js environment setup complete"
}

# Setup environment files
setup_environment_files() {
    log_info "Setting up environment files..."
    
    cd "$PROJECT_ROOT"
    
    # Copy env.example to .env if it doesn't exist
    if [ ! -f ".env" ]; then
        if [ -f "config/env.example" ]; then
            cp config/env.example .env
            log_success "Created .env from template"
            log_warning "Please edit .env with your actual values"
        else
            log_error "env.example not found"
        fi
    else
        log_info ".env already exists, skipping..."
    fi
    
    # Create environment-specific config
    cat > "config/environment.yaml" << EOF
# Environment configuration
environment: $ENVIRONMENT
debug: $([ "$ENVIRONMENT" = "development" ] && echo "true" || echo "false")
log_level: $([ "$ENVIRONMENT" = "development" ] && echo "DEBUG" || echo "INFO")

# Service endpoints
api_url: "http://localhost:8000"
ui_url: "http://localhost:3000"
webhook_url: "http://localhost:8000"

# Database
db_dsn_env: "DB_DSN"
db_pool_min: 5
db_pool_max: 20

# Redis
redis_url_env: "UPSTASH_REDISURL"
redis_queue_name: "bl1nk_tasks"

# Providers
providers:
  openrouter:
    timeout: 30
    max_retries: 3
  cloudflare:
    timeout: 30
    max_retries: 2
  bedrock:
    timeout: 60
    max_retries: 5
EOF
    
    log_success "Environment files created"
}

# Setup database
setup_database() {
    log_info "Setting up database..."
    
    cd "$PROJECT_ROOT"
    
    # Check if .env exists and has DB_DSN
    if [ ! -f ".env" ]; then
        log_warning ".env not found, skipping database setup"
        return
    fi
    
    # Source environment variables
    set -a
    source .env
    set +a
    
    # Check if DB_DSN is set
    if [ -z "$DB_DSN" ]; then
        log_warning "DB_DSN not set in .env, skipping database setup"
        return
    fi
    
    # Run migrations
    log_info "Running database migrations..."
    
    if [ -f "sql/migrations/001_create_tables.sql" ]; then
        log_info "Creating tables..."
        if psql "$DB_DSN" -f sql/migrations/001_create_tables.sql; then
            log_success "Tables created successfully"
        else
            log_error "Failed to create tables"
        fi
    fi
    
    if [ -f "sql/migrations/002_add_indexes.sql" ]; then
        log_info "Creating indexes..."
        if psql "$DB_DSN" -f sql/migrations/002_add_indexes.sql; then
            log_success "Indexes created successfully"
        else
            log_error "Failed to create indexes"
        fi
    fi
    
    # Verify setup
    log_info "Verifying database setup..."
    table_count=$(psql "$DB_DSN" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)
    log_info "Created $table_count tables"
    
    log_success "Database setup complete"
}

# Setup development tools
setup_dev_tools() {
    log_info "Setting up development tools..."
    
    cd "$PROJECT_ROOT"
    
    # Setup pre-commit hooks
    if command -v pre-commit &> /dev/null; then
        log_info "Setting up pre-commit hooks..."
        cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-merge-conflict
      - id: check-added-large-files
  
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]
  
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.270
    hooks:
      - id: ruff
  
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.40.0
    hooks:
      - id: eslint
        files: \.(js|jsx|ts|tsx)$
EOF
        
        pre-commit install
        log_success "Pre-commit hooks installed"
    fi
    
    # Create VS Code workspace settings
    mkdir -p .vscode
    cat > .vscode/settings.json << 'EOF'
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.linting.blackEnabled": true,
  "python.formatting.provider": "black",
  "python.sortImports.args": ["--profile", "black"],
  "typescript.preferences.importModuleSpecifier": "relative",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/.DS_Store": true,
    "**/.env": false
  },
  "search.exclude": {
    "**/node_modules": true,
    "**/bower_components": true,
    "**/*.code-search": true,
    "**/temp": true,
    "**/logs": true,
    "**/data": true
  }
}
EOF
    
    # Create launch configurations
    cat > .vscode/launch.json << 'EOF'
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/.venv/bin/uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      ],
      "cwd": "${workspaceFolder}/apps/worker",
      "console": "integratedTerminal",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/apps/worker"
      }
    },
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}/apps/worker"
    },
    {
      "name": "Node.js: Bridge",
      "type": "node",
      "request": "launch",
      "cwd": "${workspaceFolder}/apps/bridge",
      "runtimeArgs": ["--loader", "ts-node/esm"],
      "args": ["src/index.ts"]
    }
  ]
}
EOF
    
    log_success "Development tools setup complete"
}

# Create starter files
create_starter_files() {
    log_info "Creating starter files..."
    
    cd "$PROJECT_ROOT"
    
    # Create .gitignore
    cat > .gitignore << 'EOF'
# Environment variables
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.venv/
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

# Runtime data
pids/
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/
*.lcov

# nyc test coverage
.nyc_output

# Dependency directories
node_modules/
jspm_packages/

# TypeScript cache
*.tsbuildinfo

# Optional npm cache directory
.npm

# Optional eslint cache
.eslintcache

# Optional stylelint cache
.stylelintcache

# Microbundle cache
.rpt2_cache/
.rts2_cache_cjs/
.rts2_cache_es/
.rts2_cache_umd/

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# parcel-bundler cache (https://parceljs.org/)
.cache
.parcel-cache

# Next.js build output
.next
out

# Nuxt.js build / generate output
.nuxt
dist

# Gatsby files
.cache/
public

# Vuepress build output
.vuepress/dist

# Serverless directories
.serverless/

# FuseBox cache
.fusebox/

# DynamoDB Local files
.dynamodb/

# TernJS port file
.tern-port

# Stores VSCode versions used for testing VSCode extensions
.vscode-test

# Temporary files
temp/
tmp/

# Database
*.db
*.sqlite
*.sqlite3

# Terraform
*.tfstate
*.tfstate.*
.terraform/

# Docker
.dockerignore

# Local development
local/
EOF
    
    # Create README.md
    cat > README.md << 'EOF'
# bl1nk-agent-builder

AI Agent Platform with RAG, multi-agent, MCP integration, and compliance.

## Architecture

- **Edge**: Cloudflare Workers (proxy)
- **Core**: FastAPI (orchestrator)  
- **Database**: Neon Postgres + pgvector
- **Queue**: Upstash Redis
- **Storage**: Cloudflare R2

## Quick Start

1. **Bootstrap the project**:
   ```bash
   ./scripts/bootstrap.sh development
   ```

2. **Configure environment**:
   ```bash
   cp config/env.example .env
   # Edit .env with your actual values
   ```

3. **Setup database**:
   ```bash
   psql "$DB_DSN" -f sql/migrations/001_create_tables.sql
   psql "$DB_DSN" -f sql/migrations/002_add_indexes.sql
   ```

4. **Start services**:
   ```bash
   # Terminal 1: FastAPI
   cd apps/worker
   source ../../.venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Terminal 2: Cloudflare Worker
   cd apps/bridge
   wrangler dev
   
   # Terminal 3: Next.js UI (optional)
   cd ui/nextjs
   pnpm dev
   ```

## Project Structure

```
bl1nk-agent-builder/
├── apps/
│   ├── bridge/          # Cloudflare Worker (Edge proxy)
│   └── worker/          # FastAPI (Core)
├── packages/
│   └── schema/          # OpenAPI schema
├── sql/
│   └── migrations/      # Database migrations
├── config/              # Configuration files
├── scripts/             # Utility scripts
├── ui/                  # Next.js frontend
└── tests/               # Test files
```

## Development

- **Code Style**: Black + isort + ruff
- **Testing**: pytest + asyncio
- **Linting**: ESLint + TypeScript
- **Pre-commit**: Automatically runs formatting and linting

## API Documentation

Once running, visit:
- **FastAPI Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Resources

- [Architecture Overview](docs/architecture.md)
- [API Reference](docs/api-reference.md)
- [Deployment Guide](docs/deployment.md)
- [Contributing Guide](docs/contributing.md)
EOF
    
    # Create development documentation
    cat > docs/development.md << 'EOF'
# Development Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis (Upstash)

## Development Workflow

1. **Create a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r apps/worker/requirements.txt
   pnpm install --prefix apps/bridge
   ```

3. **Run tests**:
   ```bash
   pytest tests/ -v
   ```

4. **Format code**:
   ```bash
   black apps/worker/
   isort apps/worker/
   ```

## Database Development

1. **Run migrations**:
   ```bash
   psql "$DB_DSN" -f sql/migrations/001_create_tables.sql
   psql "$DB_DSN" -f sql/migrations/002_add_indexes.sql
   ```

2. **Reset database**:
   ```bash
   dropdb your_database_name
   createdb your_database_name
   psql "$DB_DSN" -f sql/migrations/001_create_tables.sql
   psql "$DB_DSN" -f sql/migrations/002_add_indexes.sql
   ```

## Adding New Features

1. **Update OpenAPI schema** in `packages/schema/openapi.yaml`
2. **Generate Pydantic models**:
   ```bash
   datamodel-code-generator --input packages/schema/openapi.yaml --output apps/worker/app/models/schemas_generated.py
   ```
3. **Implement routes** in `apps/worker/app/routes/`
4. **Add tests** in `tests/`
5. **Update database schema** if needed in `sql/migrations/`

## API Design Principles

- RESTful endpoints
- Idempotent operations (prevent duplicates)
- Consistent error responses
- OpenAPI schema as single source of truth
- Comprehensive logging and tracing
EOF
    
    log_success "Starter files created"
}

# Main execution
main() {
    log_info "Starting bl1nk-agent-builder bootstrap for environment: $ENVIRONMENT"
    log_info "Project root: $PROJECT_ROOT"
    
    check_prerequisites
    create_project_structure
    setup_python_environment
    setup_nodejs_environment
    setup_environment_files
    setup_database
    setup_dev_tools
    create_starter_files
    
    log_success "Bootstrap completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Edit .env with your actual values"
    echo "2. Review the configuration files in config/"
    echo "3. Start developing your agents and skills!"
    echo ""
    echo "Quick start commands:"
    echo "  # Start FastAPI server"
    echo "  cd apps/worker && source ../../.venv/bin/activate && uvicorn app.main:app --reload"
    echo ""
    echo "  # Start Cloudflare Worker"
    echo "  cd apps/bridge && wrangler dev"
    echo ""
    echo "  # Run tests"
    echo "  pytest tests/ -v"
    echo ""
}

# Run main function
main "$@"