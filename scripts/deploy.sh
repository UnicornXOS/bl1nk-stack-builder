#!/bin/bash

# =============================================================================
# bl1nk Agent Builder - Production Deployment Script
# =============================================================================
# Description: Production deployment automation with rollback capabilities
# Author: MiniMax Agent
# Version: 1.0.0
# =============================================================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DEPLOY_ENV="${1:-production}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$PROJECT_DIR/backups/deployment_$TIMESTAMP"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Environment configurations
declare -A ENV_CONFIGS
ENV_CONFIGS=(
    ["production"]="prod"
    ["staging"]="staging"
    ["development"]="dev"
)

# =============================================================================
# Utility Functions
# =============================================================================

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$PROJECT_DIR/logs/deployment.log"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$PROJECT_DIR/logs/deployment.log"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}" | tee -a "$PROJECT_DIR/logs/deployment.log"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "$PROJECT_DIR/logs/deployment.log"
}

log_info() {
    echo -e "${CYAN}[$(date '+%Y-%m-%d %H:%M:%S')] ℹ️  $1${NC}" | tee -a "$PROJECT_DIR/logs/deployment.log"
}

# =============================================================================
# Pre-deployment Checks
# =============================================================================

check_prerequisites() {
    log "🔍 Checking deployment prerequisites..."
    
    # Check required tools
    local required_tools=("docker" "docker-compose" "git" "curl")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            log_error "Required tool '$tool' is not installed"
            exit 1
        fi
    done
    
    # Check environment file
    if [[ ! -f "$PROJECT_DIR/.env" ]]; then
        log_warning "Environment file not found. Creating from template..."
        cp "$PROJECT_DIR/config/env.example" "$PROJECT_DIR/.env"
        log_warning "Please edit .env file with your configuration before continuing"
        read -p "Press Enter to continue after updating .env file..."
    fi
    
    # Validate environment variables
    if ! "$SCRIPT_DIR/validate_secrets.sh" >/dev/null 2>&1; then
        log_error "Environment validation failed. Please check your .env file"
        exit 1
    fi
    
    # Check disk space (minimum 5GB)
    local available_space
    available_space=$(df "$PROJECT_DIR" | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 5242880 ]]; then  # 5GB in KB
        log_error "Insufficient disk space. At least 5GB required"
        exit 1
    fi
    
    log_success "Prerequisites check completed"
}

check_system_resources() {
    log "💻 Checking system resources..."
    
    # Check Docker resources
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running or not accessible"
        exit 1
    fi
    
    # Check available memory (minimum 4GB)
    local available_memory
    available_memory=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    if [[ $available_memory -lt 4096 ]]; then
        log_warning "Low memory detected ($available_memory MB). Production deployment may be slow"
    fi
    
    # Check CPU cores (minimum 2)
    local cpu_cores
    cpu_cores=$(nproc)
    if [[ $cpu_cores -lt 2 ]]; then
        log_warning "Low CPU cores detected ($cpu_cores). Production deployment may be slow"
    fi
    
    log_success "System resources check completed"
}

run_pre_deployment_tests() {
    log "🧪 Running pre-deployment tests..."
    
    # Run unit tests
    if ! make test >/dev/null 2>&1; then
        log_error "Unit tests failed"
        exit 1
    fi
    
    # Run linting
    if ! make lint >/dev/null 2>&1; then
        log_error "Linting failed"
        exit 1
    fi
    
    # Security audit
    if ! make security-audit >/dev/null 2>&1; then
        log_error "Security audit failed"
        exit 1
    fi
    
    log_success "Pre-deployment tests passed"
}

# =============================================================================
# Backup Functions
# =============================================================================

create_backup() {
    log "💾 Creating deployment backup..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup database
    if docker-compose ps | grep -q postgres; then
        log "Backing up database..."
        docker-compose exec -T postgres pg_dump -U bl1nk bl1nk > "$BACKUP_DIR/database_backup.sql"
    fi
    
    # Backup configuration files
    log "Backing up configuration..."
    cp -r "$PROJECT_DIR/.env" "$BACKUP_DIR/"
    cp -r "$PROJECT_DIR/config" "$BACKUP_DIR/"
    
    # Backup application data
    log "Backing up application data..."
    if [[ -d "$PROJECT_DIR/uploads" ]]; then
        cp -r "$PROJECT_DIR/uploads" "$BACKUP_DIR/"
    fi
    
    # Backup logs
    log "Backing up logs..."
    if [[ -d "$PROJECT_DIR/logs" ]]; then
        cp -r "$PROJECT_DIR/logs" "$BACKUP_DIR/"
    fi
    
    # Create backup metadata
    cat > "$BACKUP_DIR/metadata.json" <<EOF
{
    "timestamp": "$(date -Iseconds)",
    "environment": "$DEPLOY_ENV",
    "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "git_branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')",
    "backup_size": "$(du -sh "$BACKUP_DIR" | cut -f1)"
}
EOF
    
    log_success "Backup created: $BACKUP_DIR"
}

# =============================================================================
# Database Migration
# =============================================================================

run_database_migrations() {
    log "🗄️  Running database migrations..."
    
    # Wait for database to be ready
    log "Waiting for database..."
    local max_attempts=30
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if docker-compose exec -T postgres pg_isready -U bl1nk >/dev/null 2>&1; then
            break
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    if [[ $attempt -eq $max_attempts ]]; then
        log_error "Database failed to become ready"
        exit 1
    fi
    
    # Run migrations
    if docker-compose exec -T api python -m alembic upgrade head >/dev/null 2>&1; then
        log_success "Database migrations completed"
    else
        log_error "Database migrations failed"
        exit 1
    fi
}

# =============================================================================
# Build and Deployment
# =============================================================================

build_application() {
    log "🏗️  Building application images..."
    
    # Build with no cache for production
    docker-compose build --no-cache
    
    log_success "Application images built"
}

deploy_application() {
    log "🚀 Deploying application..."
    
    # Select appropriate compose file
    local compose_file="docker-compose.yml"
    if [[ -f "docker-compose.$DEPLOY_ENV.yml" ]]; then
        compose_file="docker-compose.$DEPLOY_ENV.yml"
    fi
    
    # Pull latest images
    log "Pulling latest images..."
    docker-compose -f "$compose_file" pull
    
    # Start services
    log "Starting services..."
    docker-compose -f "$compose_file" up -d
    
    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    sleep 30
    
    # Health check
    if ! curl -f http://localhost:8000/health >/dev/null 2>&1; then
        log_error "Health check failed after deployment"
        rollback_deployment
        exit 1
    fi
    
    log_success "Application deployed successfully"
}

# =============================================================================
# Post-deployment Validation
# =============================================================================

validate_deployment() {
    log "🔍 Validating deployment..."
    
    local max_attempts=60
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        # Check API health
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            log_success "API health check passed"
            break
        fi
        
        attempt=$((attempt + 1))
        sleep 5
    done
    
    if [[ $attempt -eq $max_attempts ]]; then
        log_error "API health check failed"
        return 1
    fi
    
    # Check database connectivity
    if ! docker-compose exec -T api python -c "from app.database import engine; engine.connect()" >/dev/null 2>&1; then
        log_error "Database connectivity check failed"
        return 1
    fi
    
    log_success "Database connectivity check passed"
    
    # Check Redis connectivity
    if ! docker-compose exec -T redis redis-cli ping | grep -q PONG; then
        log_error "Redis connectivity check failed"
        return 1
    fi
    
    log_success "Redis connectivity check passed"
    
    # Run smoke tests
    if ! run_smoke_tests; then
        log_error "Smoke tests failed"
        return 1
    fi
    
    log_success "Deployment validation completed"
}

run_smoke_tests() {
    log "🧪 Running smoke tests..."
    
    # Test basic API endpoints
    local endpoints=(
        "http://localhost:8000/health"
        "http://localhost:8000/api/v1/models"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if ! curl -f "$endpoint" >/dev/null 2>&1; then
            log_error "Smoke test failed for $endpoint"
            return 1
        fi
    done
    
    log_success "Smoke tests passed"
    return 0
}

# =============================================================================
# Rollback Functions
# =============================================================================

rollback_deployment() {
    log_warning "🔄 Initiating rollback..."
    
    # Stop current deployment
    docker-compose down
    
    # Restore from backup
    if [[ -d "$BACKUP_DIR" ]]; then
        log "Restoring from backup..."
        
        # Restore database
        if [[ -f "$BACKUP_DIR/database_backup.sql" ]]; then
            log "Restoring database..."
            docker-compose up -d postgres
            sleep 10
            cat "$BACKUP_DIR/database_backup.sql" | docker-compose exec -T postgres psql -U bl1nk bl1nk
        fi
        
        # Restore configuration
        if [[ -f "$BACKUP_DIR/.env" ]]; then
            cp "$BACKUP_DIR/.env" "$PROJECT_DIR/"
        fi
    fi
    
    # Redeploy previous version (if available)
    log "Redeploying previous version..."
    docker-compose up -d
    
    log_success "Rollback completed"
}

# =============================================================================
# Monitoring Setup
# =============================================================================

setup_monitoring() {
    log "📊 Setting up monitoring..."
    
    # Check if monitoring services are running
    if ! curl -f http://localhost:9090 >/dev/null 2>&1; then
        log_warning "Prometheus not accessible"
    else
        log_success "Prometheus monitoring active"
    fi
    
    if ! curl -f http://localhost:3001 >/dev/null 2>&1; then
        log_warning "Grafana not accessible"
    else
        log_success "Grafana monitoring active"
    fi
    
    # Start billing monitor
    if ! docker-compose ps | grep -q billing-monitor; then
        log "Starting billing monitor..."
        docker-compose up -d billing-monitor
    fi
}

# =============================================================================
# Notification Functions
# =============================================================================

send_deployment_notification() {
    local status=$1
    local message=$2
    
    # Slack notification (if configured)
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local color
        case $status in
            "success") color="good" ;;
            "error") color="danger" ;;
            "warning") color="warning" ;;
            *) color="#439FE0" ;;
        esac
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"bl1nk Deployment $status\",
                    \"text\": \"$message\",
                    \"fields\": [
                        {\"title\": \"Environment\", \"value\": \"$DEPLOY_ENV\", \"short\": true},
                        {\"title\": \"Timestamp\", \"value\": \"$(date -Iseconds)\", \"short\": true}
                    ]
                }]
            }" \
            "$SLACK_WEBHOOK_URL" || true
    fi
    
    # Email notification (if configured)
    if [[ -n "${DEPLOYMENT_EMAIL:-}" ]]; then
        echo "$message" | mail -s "bl1nk Deployment $status" "$DEPLOYMENT_EMAIL" || true
    fi
    
    log "📢 Deployment notification sent"
}

# =============================================================================
# Cleanup Functions
# =============================================================================

cleanup() {
    log "🧹 Cleaning up old resources..."
    
    # Remove unused Docker images
    docker image prune -f
    
    # Remove unused volumes
    docker volume prune -f
    
    # Clean old backups (keep last 10)
    if [[ -d "$PROJECT_DIR/backups" ]]; then
        cd "$PROJECT_DIR/backups"
        ls -1t | tail -n +11 | xargs -r rm -rf
    fi
    
    log_success "Cleanup completed"
}

# =============================================================================
# Main Deployment Functions
# =============================================================================

deploy_staging() {
    log "🚀 Deploying to staging environment..."
    
    check_prerequisites
    check_system_resources
    create_backup
    run_pre_deployment_tests
    build_application
    deploy_application
    validate_deployment
    setup_monitoring
    
    send_deployment_notification "success" "Staging deployment completed successfully"
    log_success "✅ Staging deployment completed!"
}

deploy_production() {
    log "🚀 Deploying to production environment..."
    
    # Production requires confirmation
    echo -e "${RED}⚠️  PRODUCTION DEPLOYMENT ⚠️${NC}"
    echo "This will deploy to production. Are you sure?"
    read -p "Type 'CONFIRM' to proceed: " confirmation
    
    if [[ "$confirmation" != "CONFIRM" ]]; then
        log_warning "Production deployment cancelled"
        exit 0
    fi
    
    check_prerequisites
    check_system_resources
    run_pre_deployment_tests
    create_backup
    build_application
    
    # Production deployment with additional safety checks
    log "Deploying to production..."
    deploy_application
    
    # Extended validation for production
    if ! validate_deployment; then
        log_error "Production deployment validation failed"
        rollback_deployment
        send_deployment_notification "error" "Production deployment failed - rollback completed"
        exit 1
    fi
    
    setup_monitoring
    cleanup
    
    send_deployment_notification "success" "Production deployment completed successfully"
    log_success "✅ Production deployment completed!"
}

# =============================================================================
# Status and Monitoring
# =============================================================================

show_deployment_status() {
    log "📊 Deployment Status:"
    
    echo -e "\n${CYAN}Services Status:${NC}"
    docker-compose ps
    
    echo -e "\n${CYAN}Recent Logs:${NC}"
    docker-compose logs --tail=20
    
    echo -e "\n${CYAN}Health Check:${NC}"
    curl -s http://localhost:8000/health | jq . 2>/dev/null || echo "API not responding"
    
    echo -e "\n${CYAN}Resource Usage:${NC}"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
}

# =============================================================================
# Main Script Logic
# =============================================================================

main() {
    # Create logs directory
    mkdir -p "$PROJECT_DIR/logs"
    
    log "🚀 bl1nk Agent Builder - Deployment Script"
    log "Environment: $DEPLOY_ENV"
    log "Timestamp: $TIMESTAMP"
    
    case "$DEPLOY_ENV" in
        "production"|"prod")
            deploy_production
            ;;
        "staging"|"stage")
            deploy_staging
            ;;
        "development"|"dev")
            log "🚀 Deploying to development environment..."
            check_prerequisites
            build_application
            deploy_application
            log_success "✅ Development deployment completed!"
            ;;
        "status")
            show_deployment_status
            ;;
        "rollback")
            if [[ -z "${2:-}" ]]; then
                log_error "Please specify backup directory for rollback"
                exit 1
            fi
            BACKUP_DIR="$2"
            rollback_deployment
            ;;
        *)
            echo -e "${YELLOW}Usage: $0 [production|staging|development|status|rollback]${NC}"
            echo ""
            echo "Commands:"
            echo "  production  - Deploy to production environment"
            echo "  staging     - Deploy to staging environment"
            echo "  development - Deploy to development environment"
            echo "  status      - Show deployment status"
            echo "  rollback    - Rollback to previous deployment"
            echo ""
            echo "Examples:"
            echo "  $0 production    # Deploy to production"
            echo "  $0 staging       # Deploy to staging"
            echo "  $0 status        # Show current status"
            echo "  $0 rollback /path/to/backup  # Rollback to backup"
            exit 1
            ;;
    esac
}

# Check if running in CI/CD environment
if [[ "${CI:-false}" == "true" ]]; then
    # In CI/CD, skip interactive prompts
    main "$@"
else
    # Interactive mode
    main "$@"
fi