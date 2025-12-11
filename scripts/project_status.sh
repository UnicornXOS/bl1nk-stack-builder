#!/bin/bash

# =============================================================================
# bl1nk Agent Builder - Project Status Checker
# =============================================================================
# Description: Quick project health and status overview
# Author: MiniMax Agent
# Version: 1.0.0
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# =============================================================================
# Utility Functions
# =============================================================================

print_header() {
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}  🚀 bl1nk Agent Builder - Project Status Dashboard ${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo
}

print_section() {
    echo -e "\n${CYAN}📊 $1${NC}"
    echo "$(printf '=%.0s' {1..60})"
}

print_status() {
    local status=$1
    local message=$2
    case $status in
        "✅") echo -e "  ${GREEN}✅ $message${NC}" ;;
        "⚠️") echo -e "  ${YELLOW}⚠️  $message${NC}" ;;
        "❌") echo -e "  ${RED}❌ $message${NC}" ;;
        "🔧") echo -e "  ${BLUE}🔧 $message${NC}" ;;
        "📁") echo -e "  ${CYAN}📁 $message${NC}" ;;
    esac
}

# =============================================================================
# Project Statistics
# =============================================================================

show_project_stats() {
    print_section "Project Statistics"
    
    # File count
    local total_files
    total_files=$(find "$PROJECT_DIR" -type f | wc -l)
    print_status "📁" "Total Files: $total_files"
    
    # Code lines
    local code_lines
    code_lines=$(find "$PROJECT_DIR" -name "*.py" -o -name "*.ts" -o -name "*.js" -o -name "*.sh" | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo "0")
    print_status "📝" "Lines of Code: $code_lines+"
    
    # Documentation files
    local doc_files
    doc_files=$(find "$PROJECT_DIR" -name "*.md" | wc -l)
    print_status "📚" "Documentation Files: $doc_files"
    
    # Scripts
    local script_files
    script_files=$(find "$PROJECT_DIR/scripts" -name "*.sh" | wc -l)
    print_status "🔧" "Utility Scripts: $script_files"
    
    # Configuration files
    local config_files
    config_files=$(find "$PROJECT_DIR/config" -name "*.yaml" -o -name "*.yml" -o -name "*.json" | wc -l)
    print_status "⚙️" "Configuration Files: $config_files"
}

# =============================================================================
# Development Status
# =============================================================================

show_development_status() {
    print_section "Development Environment"
    
    # Check Docker
    if command -v docker >/dev/null 2>&1; then
        print_status "✅" "Docker: Available"
        if docker info >/dev/null 2>&1; then
            print_status "✅" "Docker: Running"
        else
            print_status "⚠️" "Docker: Not running"
        fi
    else
        print_status "❌" "Docker: Not installed"
    fi
    
    # Check Docker Compose
    if command -v docker-compose >/dev/null 2>&1; then
        print_status "✅" "Docker Compose: Available"
    else
        print_status "❌" "Docker Compose: Not installed"
    fi
    
    # Check Python
    if command -v python3 >/dev/null 2>&1; then
        local python_version
        python_version=$(python3 --version | awk '{print $2}')
        print_status "✅" "Python: $python_version"
    else
        print_status "❌" "Python: Not installed"
    fi
    
    # Check Node.js
    if command -v node >/dev/null 2>&1; then
        local node_version
        node_version=$(node --version)
        print_status "✅" "Node.js: $node_version"
    else
        print_status "❌" "Node.js: Not installed"
    fi
    
    # Check required tools
    local tools=("curl" "jq" "git")
    for tool in "${tools[@]}"; do
        if command -v "$tool" >/dev/null 2>&1; then
            print_status "✅" "$tool: Available"
        else
            print_status "⚠️" "$tool: Not installed (optional)"
        fi
    done
}

# =============================================================================
# Configuration Status
# =============================================================================

show_configuration_status() {
    print_section "Configuration Status"
    
    # Environment file
    if [[ -f "$PROJECT_DIR/.env" ]]; then
        print_status "✅" "Environment file: Found"
        
        # Check critical environment variables
        local critical_vars=("OPENROUTER_TOKEN" "CLOUDFLARE_API_TOKEN" "DB_DSN")
        for var in "${critical_vars[@]}"; do
            if grep -q "^$var=" "$PROJECT_DIR/.env" && ! grep -q "^$var=your-" "$PROJECT_DIR/.env"; then
                print_status "✅" "$var: Configured"
            else
                print_status "⚠️" "$var: Not configured"
            fi
        done
    else
        print_status "⚠️" "Environment file: Not found (copy from env.example)"
    fi
    
    # Configuration files
    local config_files=(
        "config/billing_thresholds.yaml"
        "config/monthly_budget.yaml"
        "config/provider_routing.yaml"
        "config/providermodels.yaml"
    )
    
    for config in "${config_files[@]}"; do
        if [[ -f "$PROJECT_DIR/$config" ]]; then
            print_status "✅" "$config: Found"
        else
            print_status "⚠️" "$config: Missing"
        fi
    done
}

# =============================================================================
# Service Status
# =============================================================================

show_service_status() {
    print_section "Service Status"
    
    # Check if docker-compose is available
    if ! command -v docker-compose >/dev/null 2>&1; then
        print_status "⚠️" "Docker Compose not available - cannot check services"
        return
    fi
    
    cd "$PROJECT_DIR"
    
    # Check if docker-compose.yml exists
    if [[ ! -f "docker-compose.yml" ]]; then
        print_status "❌" "docker-compose.yml not found"
        return
    fi
    
    # Check running services
    if docker-compose ps | grep -q "Up"; then
        print_status "✅" "Services: Running"
        
        # Show running containers
        echo "  Active containers:"
        docker-compose ps --services --filter "status=running" | while read -r service; do
            print_status "🔧" "  - $service"
        done
    else
        print_status "⚠️" "Services: Not running (run 'make dev' to start)"
    fi
    
    # Check service health endpoints
    local endpoints=(
        "http://localhost:8000/health:API"
        "http://localhost:3000:Admin"
        "http://localhost:3001:Grafana"
        "http://localhost:9090:Prometheus"
    )
    
    echo "  Health checks:"
    for endpoint_info in "${endpoints[@]}"; do
        local endpoint=$(echo "$endpoint_info" | cut -d: -f1-2)
        local name=$(echo "$endpoint_info" | cut -d: -f3)
        
        if curl -f -s --max-time 2 "$endpoint" >/dev/null 2>&1; then
            print_status "✅" "  $name: Healthy"
        else
            print_status "⚠️" "  $name: Not responding"
        fi
    done
}

# =============================================================================
# Monitoring Status
# =============================================================================

show_monitoring_status() {
    print_section "Monitoring & Billing"
    
    # Check billing monitor script
    if [[ -f "$PROJECT_DIR/scripts/billing_monitor.sh" ]]; then
        print_status "✅" "Billing Monitor: Available"
        
        # Check configuration
        if [[ -f "$PROJECT_DIR/config/billing_thresholds.yaml" ]]; then
            print_status "✅" "Billing Config: Found"
        else
            print_status "⚠️" "Billing Config: Missing (run 'make billing-config')"
        fi
        
        # Check reports directory
        if [[ -d "$PROJECT_DIR/reports" ]] && [[ "$(ls -A "$PROJECT_DIR/reports" 2>/dev/null)" ]]; then
            print_status "✅" "Billing Reports: Generated"
        else
            print_status "⚠️" "Billing Reports: No reports yet"
        fi
    else
        print_status "❌" "Billing Monitor: Not found"
    fi
    
    # Check monitoring services
    local monitoring_services=("prometheus" "grafana")
    for service in "${monitoring_services[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$service"; then
            print_status "✅" "$service: Running"
        else
            print_status "⚠️" "$service: Not running"
        fi
    done
}

# =============================================================================
# Documentation Status
# =============================================================================

show_documentation_status() {
    print_section "Documentation"
    
    local docs=(
        "README.md:Main Documentation"
        "QUICK_START_GUIDE.md:Quick Start"
        "AGENTS.md:AI Agent Guide"
        "PROJECT_SUMMARY.md:Project Status"
        "SECURITY.md:Security Guide"
        "API_KEYS_GUIDE.md:API Key Guide"
        "docs/ADMIN_DASHBOARD.md:Admin Guide"
    )
    
    for doc_info in "${docs[@]}"; do
        local doc_path=$(echo "$doc_info" | cut -d: -f1)
        local doc_name=$(echo "$doc_info" | cut -d: -f2)
        
        if [[ -f "$PROJECT_DIR/$doc_path" ]]; then
            print_status "✅" "$doc_name: Available"
        else
            print_status "⚠️" "$doc_name: Missing"
        fi
    done
}

# =============================================================================
# Next Steps
# =============================================================================

show_next_steps() {
    print_section "🚀 Next Steps"
    
    echo "To get started with bl1nk Agent Builder:"
    echo
    echo -e "${CYAN}1. Quick Setup:${NC}"
    echo "   make install        # Install dependencies"
    echo "   make dev-setup      # Setup development environment"
    echo
    echo -e "${CYAN}2. Configure API Keys:${NC}"
    echo "   cp config/env.example .env"
    echo "   # Edit .env with your API keys"
    echo
    echo -e "${CYAN}3. Start Development:${NC}"
    echo "   make dev            # Start all services"
    echo
    echo -e "${CYAN}4. Monitor Costs:${NC}"
    echo "   make billing-config # Setup billing monitoring"
    echo "   make billing-check  # Check current costs"
    echo
    echo -e "${CYAN}5. Deploy to Production:${NC}"
    echo "   make deploy         # Deploy to production"
    echo
    echo -e "${YELLOW}📖 For detailed instructions, see QUICK_START_GUIDE.md${NC}"
}

# =============================================================================
# Quick Commands
# =============================================================================

show_quick_commands() {
    print_section "⚡ Quick Commands"
    
    echo "Development:"
    echo "  make install        # Install dependencies"
    echo "  make dev            # Start development environment"
    echo "  make test           # Run tests"
    echo "  make lint           # Code quality check"
    echo
    echo "Database:"
    echo "  make db-migrate     # Run migrations"
    echo "  make db-shell       # Open database shell"
    echo "  make db-backup      # Backup database"
    echo
    echo "Monitoring:"
    echo "  make billing-check  # Check costs"
    echo "  make monitoring     # View monitoring"
    echo "  make health         # Health check"
    echo
    echo "Deployment:"
    echo "  make deploy         # Deploy to production"
    echo "  make prod           # Start production"
    echo "  make status         # Show deployment status"
    echo
    echo "Utilities:"
    echo "  make clean          # Clean up containers"
    echo "  make project-stats  # Show project statistics"
    echo "  make verify-setup   # Verify project setup"
}

# =============================================================================
# System Requirements Check
# =============================================================================

show_system_requirements() {
    print_section "🖥️ System Requirements"
    
    # Check OS
    local os_name
    case "$(uname -s)" in
        Linux*) os_name="Linux" ;;
        Darwin*) os_name="macOS" ;;
        CYGWIN*|MINGW*|MSYS*) os_name="Windows" ;;
        *) os_name="Unknown" ;;
    esac
    print_status "🖥️" "Operating System: $os_name"
    
    # Check memory
    local memory_gb
    memory_gb=$(free -g | awk 'NR==2{printf "%.1f", $2}')
    if (( $(echo "$memory_gb >= 4" | bc -l 2>/dev/null || echo "0") )); then
        print_status "✅" "Memory: ${memory_gb}GB (Good)"
    else
        print_status "⚠️" "Memory: ${memory_gb}GB (Minimum 4GB recommended)"
    fi
    
    # Check disk space
    local disk_gb
    disk_gb=$(df -BG . | awk 'NR==2{print $4}' | sed 's/G//')
    if [[ $disk_gb -ge 10 ]]; then
        print_status "✅" "Disk Space: ${disk_gb}GB (Good)"
    else
        print_status "⚠️" "Disk Space: ${disk_gb}GB (Minimum 10GB recommended)"
    fi
    
    # Check CPU cores
    local cpu_cores
    cpu_cores=$(nproc)
    if [[ $cpu_cores -ge 2 ]]; then
        print_status "✅" "CPU Cores: $cpu_cores (Good)"
    else
        print_status "⚠️" "CPU Cores: $cpu_cores (Minimum 2 recommended)"
    fi
}

# =============================================================================
# Main Function
# =============================================================================

main() {
    print_header
    
    show_project_stats
    show_system_requirements
    show_development_status
    show_configuration_status
    show_service_status
    show_monitoring_status
    show_documentation_status
    show_quick_commands
    show_next_steps
    
    echo
    echo -e "${GREEN}✅ Project Status Check Complete!${NC}"
    echo
}

# Run main function
main "$@"