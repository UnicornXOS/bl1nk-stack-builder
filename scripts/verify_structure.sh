#!/bin/bash

# =============================================================================
# bl1nk-agent-builder Structure Verification Script
# =============================================================================
# This script verifies that all required files and directories exist
# according to the project structure specification
#
# Usage: ./scripts/verify_structure.sh
# Exit codes: 0 = success, 1 = missing files found
# =============================================================================

set -e

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

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
MISSING_FILES=()

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Function to check if file/directory exists
check_file() {
    local file_path="$1"
    local description="$2"
    local required="${3:-true}"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -e "$file_path" ]; then
        if [ "$required" = "true" ]; then
            log_success "✓ $description: $file_path"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
        else
            log_info "✓ $description (optional): $file_path"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
        fi
    else
        if [ "$required" = "true" ]; then
            log_error "✗ MISSING: $description: $file_path"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            MISSING_FILES+=("$file_path")
        else
            log_warning "○ Missing (optional): $description: $file_path"
        fi
    fi
}

# Function to check directory structure
check_directory() {
    local dir_path="$1"
    local description="$2"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -d "$dir_path" ]; then
        log_success "✓ $description: $dir_path"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        log_error "✗ MISSING DIRECTORY: $description: $dir_path"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        MISSING_FILES+=("$dir_path")
    fi
}

# Function to check file content (basic validation)
check_file_content() {
    local file_path="$1"
    local pattern="$2"
    local description="$3"
    
    if [ ! -f "$file_path" ]; then
        log_error "✗ Cannot check content - file missing: $file_path"
        return 1
    fi
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if grep -q "$pattern" "$file_path" 2>/dev/null; then
        log_success "✓ $description: $file_path"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        log_error "✗ CONTENT MISSING: $description in $file_path"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        MISSING_FILES+=("$file_path (missing: $pattern)")
    fi
}

echo ""
log_info "Starting bl1nk-agent-builder structure verification..."
log_info "Project root: $PROJECT_ROOT"
echo ""

# =============================================================================
# DIRECTORY STRUCTURE VERIFICATION
# =============================================================================

echo "=== DIRECTORY STRUCTURE ==="
log_info "Checking directory structure..."

# Main directories
check_directory "." "Project root"
check_directory "apps" "Applications directory"
check_directory "apps/bridge" "Bridge app directory"
check_directory "apps/worker" "Worker app directory"
check_directory "packages" "Packages directory"
check_directory "packages/schema" "Schema package directory"
check_directory "sql" "SQL directory"
check_directory "sql/migrations" "Migrations directory"
check_directory "config" "Configuration directory"
check_directory "docs" "Documentation directory"
check_directory "scripts" "Scripts directory"
check_directory "tests" "Tests directory"
check_directory "ui" "UI directory"
check_directory "ui/nextjs" "Next.js UI directory"

echo ""

# =============================================================================
# CRITICAL FILES VERIFICATION
# =============================================================================

echo "=== CRITICAL FILES ==="
log_info "Checking critical files..."

# OpenAPI Schema (MUST exist)
check_file "packages/schema/openapi.yaml" "OpenAPI schema" "true"

# Database migrations (MUST exist)
check_file "sql/migrations/001_create_tables.sql" "Database tables migration" "true"
check_file "sql/migrations/002_add_indexes.sql" "Database indexes migration" "true"

# Configuration files
check_file "config/env.example" "Environment template" "true"
check_file "config/provider_routing.yaml" "Provider routing config" "true"
check_file "config/providermodels.yaml" "Provider models config" "true"

echo ""

# =============================================================================
# BRIDGE APP FILES VERIFICATION
# =============================================================================

echo "=== BRIDGE APP (Cloudflare Worker) ==="
log_info "Checking bridge app files..."

# Package files
check_file "apps/bridge/package.json" "Bridge package.json" "true"
check_file "apps/bridge/wrangler.toml" "Wrangler configuration" "true"
check_file "apps/bridge/tsconfig.json" "TypeScript config" "true"

# Source files
check_file "apps/bridge/src/index.ts" "Bridge main entry" "true"
check_file "apps/bridge/src/signature.ts" "Signature verification" "true"
check_file "apps/bridge/src/map_payload.ts" "Payload mapping" "true"

echo ""

# =============================================================================
# WORKER APP FILES VERIFICATION
# =============================================================================

echo "=== WORKER APP (FastAPI) ==="
log_info "Checking worker app files..."

# Package files
check_file "apps/worker/requirements.in" "Python requirements.in" "true"
check_file "apps/worker/requirements.txt" "Python requirements.txt" "true"
check_file "apps/worker/env.example" "Worker environment template" "true"

# Main application files
check_file "apps/worker/app/main.py" "FastAPI main entry" "true"
check_file "apps/worker/app/config/settings.py" "Settings configuration" "true"

# Route files
check_file "apps/worker/app/routes/__init__.py" "Routes init" "false"
check_file "apps/worker/app/routes/webhook_poe.py" "Poe webhook route" "true"
check_file "apps/worker/app/routes/webhook_manus.py" "Manus webhook route" "true"
check_file "apps/worker/app/routes/webhook_slack.py" "Slack webhook route" "true"
check_file "apps/worker/app/routes/webhook_github.py" "GitHub webhook route" "true"
check_file "apps/worker/app/routes/tasks.py" "Tasks route" "true"
check_file "apps/worker/app/routes/skills.py" "Skills route" "true"
check_file "apps/worker/app/routes/mcp.py" "MCP route" "true"
check_file "apps/worker/app/routes/health.py" "Health route" "true"
check_file "apps/worker/app/routes/admin.py" "Admin route" "true"

# Service files
check_file "apps/worker/app/services/__init__.py" "Services init" "false"
check_file "apps/worker/app/services/task_orchestrator.py" "Task orchestrator" "true"
check_file "apps/worker/app/services/processor.py" "Task processor" "true"
check_file "apps/worker/app/services/embed_client.py" "Embedding client" "true"
check_file "apps/worker/app/services/vector_store.py" "Vector store" "true"
check_file "apps/worker/app/services/llm_client.py" "LLM client" "true"
check_file "apps/worker/app/services/provider_manager.py" "Provider manager" "true"
check_file "apps/worker/app/services/billing.py" "Billing service" "true"
check_file "apps/worker/app/services/oauth.py" "OAuth service" "true"
check_file "apps/worker/app/services/github_app.py" "GitHub App service" "true"

# Model files
check_file "apps/worker/app/models/__init__.py" "Models init" "false"
check_file "apps/worker/app/models/schemas.py" "Pydantic schemas" "true"
check_file "apps/worker/app/models/database.py" "Database models" "true"

# Utility files
check_file "apps/worker/app/utils/__init__.py" "Utils init" "false"
check_file "apps/worker/app/utils/sse.py" "SSE utilities" "true"
check_file "apps/worker/app/utils/idempotency.py" "Idempotency utilities" "true"
check_file "apps/worker/app/utils/tracing.py" "Tracing utilities" "true"
check_file "apps/worker/app/utils/retry.py" "Retry utilities" "true"

# Database files
check_file "apps/worker/app/database/__init__.py" "Database init" "false"
check_file "apps/worker/app/database/connection.py" "Database connection" "true"
check_file "apps/worker/app/database/redis.py" "Redis connection" "true"

# Middleware files
check_file "apps/worker/app/middleware/__init__.py" "Middleware init" "false"
check_file "apps/worker/app/middleware/cors.py" "CORS middleware" "true"
check_file "apps/worker/app/middleware/auth.py" "Auth middleware" "true"
check_file "apps/worker/app/middleware/tracing.py" "Tracing middleware" "true"

# Metrics files
check_file "apps/worker/app/routes/metrics.py" "Metrics route" "true"

echo ""

# =============================================================================
# CONFIGURATION FILES VERIFICATION
# =============================================================================

echo "=== CONFIGURATION FILES ==="
log_info "Checking configuration files..."

# Root config files
check_file "README.md" "README file" "true"
check_file ".gitignore" "Git ignore file" "true"

# Bootstrap and scripts
check_file "scripts/bootstrap.sh" "Bootstrap script" "true"
check_file "scripts/verify_structure.sh" "Structure verification script" "true"

# Environment files
check_file ".env" "Environment file" "false"  # Optional - may not exist in new setup

# VS Code configuration
check_file ".vscode/settings.json" "VS Code settings" "false"
check_file ".vscode/launch.json" "VS Code launch config" "false"

# Pre-commit configuration
check_file ".pre-commit-config.yaml" "Pre-commit config" "false"

echo ""

# =============================================================================
# CONTENT VALIDATION
# =============================================================================

echo "=== CONTENT VALIDATION ==="
log_info "Validating file contents..."

# Validate OpenAPI schema
check_file_content "packages/schema/openapi.yaml" "openapi:" "OpenAPI version declaration"
check_file_content "packages/schema/openapi.yaml" "paths:" "API paths definition"

# Validate Python requirements
check_file_content "apps/worker/requirements.txt" "fastapi" "FastAPI dependency"
check_file_content "apps/worker/requirements.txt" "asyncpg" "AsyncPG dependency"

# Validate TypeScript config
check_file_content "apps/bridge/tsconfig.json" "compilerOptions" "TypeScript compiler options"

# Validate package.json
check_file_content "apps/bridge/package.json" "\"name\":" "Package name"
check_file_content "apps/bridge/package.json" "\"scripts\":" "Package scripts"

# Validate Python main file
check_file_content "apps/worker/app/main.py" "from fastapi import" "FastAPI imports"
check_file_content "apps/worker/app/main.py" "app = FastAPI" "FastAPI app creation"

# Validate database migration
check_file_content "sql/migrations/001_create_tables.sql" "CREATE TABLE" "Table creation"
check_file_content "sql/migrations/001_create_tables.sql" "CREATE EXTENSION" "Extension creation"

# Validate provider routing config
check_file_content "config/provider_routing.yaml" "providers:" "Providers definition"

# Validate bootstrap script
check_file_content "scripts/bootstrap.sh" "#!/bin/bash" "Shebang"
check_file_content "scripts/bootstrap.sh" "create_project_structure" "Project structure function"

echo ""

# =============================================================================
# SUMMARY
# =============================================================================

echo "=== VERIFICATION SUMMARY ==="
log_info "Total checks performed: $TOTAL_CHECKS"
log_success "Passed: $PASSED_CHECKS"
if [ $FAILED_CHECKS -gt 0 ]; then
    log_error "Failed: $FAILED_CHECKS"
else
    log_info "Failed: $FAILED_CHECKS"
fi

if [ $FAILED_CHECKS -gt 0 ]; then
    echo ""
    log_error "MISSING FILES/DIRECTORIES:"
    for missing in "${MISSING_FILES[@]}"; do
        log_error "  - $missing"
    done
    echo ""
    log_error "Please run './scripts/bootstrap.sh' to create missing structure"
    exit 1
else
    echo ""
    log_success "✅ All structure verification checks passed!"
    log_success "The project structure is complete and ready for development."
    echo ""
    exit 0
fi