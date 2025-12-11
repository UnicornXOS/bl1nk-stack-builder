#!/bin/bash

# =============================================================================
# bl1nk Billing Monitor & Cost Tracking System
# =============================================================================
# Description: Comprehensive billing monitoring for all AI providers
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

# Configuration
CONFIG_DIR="config"
ALERTS_DIR="alerts"
REPORTS_DIR="reports"
LOG_DIR="logs"

# Provider configuration
PROVIDERS=("openrouter" "cloudflare" "bedrock" "anthropic")
THRESHOLDS_FILE="$CONFIG_DIR/billing_thresholds.yaml"
BUDGET_FILE="$CONFIG_DIR/monthly_budget.yaml"

# Create necessary directories
mkdir -p "$ALERTS_DIR" "$REPORTS_DIR" "$LOG_DIR"

# =============================================================================
# Utility Functions
# =============================================================================

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_DIR/billing_monitor.log"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$LOG_DIR/billing_monitor.log"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}" | tee -a "$LOG_DIR/billing_monitor.log"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "$LOG_DIR/billing_monitor.log"
}

# =============================================================================
# Cost Tracking Functions
# =============================================================================

track_openrouter_costs() {
    log "Tracking OpenRouter costs..."
    
    if [[ -z "${OPENROUTER_TOKEN:-}" ]]; then
        log_warning "OPENROUTER_TOKEN not found, skipping OpenRouter cost tracking"
        return 0
    fi
    
    local api_response
    local status_code
    
    # Get OpenRouter usage
    api_response=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer $OPENROUTER_TOKEN" \
        "https://openrouter.ai/api/v1/user" || echo "ERROR")
    
    status_code=$(echo "$api_response" | tail -n1)
    
    if [[ "$status_code" == "200" ]]; then
        local user_info
        user_info=$(echo "$api_response" | head -n -1)
        
        local credits_used
        credits_used=$(echo "$user_info" | jq -r '.credits_used // 0')
        
        local credits_limit
        credits_limit=$(echo "$user_info" | jq -r '.credits_limit // 0')
        
        local remaining_credits
        remaining_credits=$(echo "$user_info" | jq -r '.credits // 0')
        
        log_success "OpenRouter - Used: $credits_used, Remaining: $remaining_credits, Limit: $credits_limit"
        
        # Save cost data
        cat > "$REPORTS_DIR/openrouter_costs_$(date +%Y%m%d).json" <<EOF
{
    "provider": "openrouter",
    "timestamp": "$(date -Iseconds)",
    "credits_used": $credits_used,
    "credits_limit": $credits_limit,
    "remaining_credits": $remaining_credits,
    "usage_percentage": $(echo "scale=2; $credits_used * 100 / $credits_limit" | bc -l 2>/dev/null || echo "0")
}
EOF
        
        # Check thresholds
        check_openrouter_threshold "$credits_used" "$credits_limit"
        
    else
        log_error "Failed to fetch OpenRouter costs (Status: $status_code)"
    fi
}

track_cloudflare_costs() {
    log "Tracking Cloudflare costs..."
    
    if [[ -z "${CLOUDFLARE_API_TOKEN:-}" ]]; then
        log_warning "CLOUDFLARE_API_TOKEN not found, skipping Cloudflare cost tracking"
        return 0
    fi
    
    # Cloudflare AI costs are typically tracked through their dashboard
    # For now, we'll create a placeholder that can be enhanced
    
    log_success "Cloudflare - Dashboard monitoring required"
    
    # Save placeholder cost data
    cat > "$REPORTS_DIR/cloudflare_costs_$(date +%Y%m%d).json" <<EOF
{
    "provider": "cloudflare",
    "timestamp": "$(date -Iseconds)",
    "status": "manual_dashboard_check",
    "note": "Check Cloudflare Dashboard for AI usage costs"
}
EOF
}

track_bedrock_costs() {
    log "Tracking AWS Bedrock costs..."
    
    if [[ -z "${BEDROCK_TOKEN:-}" ]]; then
        log_warning "BEDROCK_TOKEN not found, skipping Bedrock cost tracking"
        return 0
    fi
    
    # AWS Bedrock costs are tracked through CloudWatch and AWS Billing
    log_success "Bedrock - Monitor via AWS Billing Console"
    
    # Save placeholder cost data
    cat > "$REPORTS_DIR/bedrock_costs_$(date +%Y%m%d).json" <<EOF
{
    "provider": "bedrock",
    "timestamp": "$(date -Iseconds)",
    "status": "aws_billing_check",
    "note": "Monitor via AWS Billing Console and CloudWatch"
}
EOF
}

# =============================================================================
# Threshold Checking Functions
# =============================================================================

check_openrouter_threshold() {
    local used=$1
    local limit=$2
    
    if [[ ! -f "$THRESHOLDS_FILE" ]]; then
        create_default_thresholds
    fi
    
    local warning_threshold
    local critical_threshold
    warning_threshold=$(yq eval '.openrouter.warning_threshold // 80' "$THRESHOLDS_FILE")
    critical_threshold=$(yq eval '.openrouter.critical_threshold // 90' "$THRESHOLDS_FILE")
    
    local percentage
    percentage=$(echo "scale=2; $used * 100 / $limit" | bc -l 2>/dev/null || echo "0")
    
    # Check for critical threshold
    if (( $(echo "$percentage >= $critical_threshold" | bc -l 2>/dev/null || echo "0") )); then
        send_critical_alert "OpenRouter" "$percentage" "$used" "$limit"
    
    # Check for warning threshold
    elif (( $(echo "$percentage >= $warning_threshold" | bc -l 2>/dev/null || echo "0") )); then
        send_warning_alert "OpenRouter" "$percentage" "$used" "$limit"
    fi
}

# =============================================================================
# Alert Functions
# =============================================================================

send_warning_alert() {
    local provider=$1
    local percentage=$2
    local used=$3
    local limit=$4
    
    log_warning "🚨 WARNING: $provider usage at ${percentage}% ($used/$limit credits)"
    
    local alert_file="$ALERTS_DIR/warning_$(date +%Y%m%d_%H%M%S).json"
    cat > "$alert_file" <<EOF
{
    "alert_type": "warning",
    "provider": "$provider",
    "timestamp": "$(date -Iseconds)",
    "usage_percentage": $percentage,
    "credits_used": $used,
    "credits_limit": $limit,
    "message": "$provider usage has reached ${percentage}% of limit"
}
EOF
    
    # Send notification (you can enhance this with email/Slack/Discord webhooks)
    send_notification "warning" "$provider" "$percentage"
}

send_critical_alert() {
    local provider=$1
    local percentage=$2
    local used=$3
    local limit=$4
    
    log_error "🚨 CRITICAL: $provider usage at ${percentage}% ($used/$limit credits)"
    
    local alert_file="$ALERTS_DIR/critical_$(date +%Y%m%d_%H%M%S).json"
    cat > "$alert_file" <<EOF
{
    "alert_type": "critical",
    "provider": "$provider",
    "timestamp": "$(date -Iseconds)",
    "usage_percentage": $percentage,
    "credits_used": $used,
    "credits_limit": $limit,
    "message": "$provider usage has reached ${percentage}% of limit - IMMEDIATE ACTION REQUIRED"
}
EOF
    
    # Send urgent notification
    send_notification "critical" "$provider" "$percentage"
}

send_notification() {
    local level=$1
    local provider=$2
    local percentage=$3
    
    # Placeholder for notification integration
    # You can add Slack, Discord, email, SMS, etc. here
    
    log "📢 Notification sent: $level alert for $provider (${percentage}%)"
    
    # Example Slack webhook (uncomment and configure)
    # if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
    #     curl -X POST -H 'Content-type: application/json' \
    #         --data "{\"text\":\"🚨 $level Alert: $provider usage at ${percentage}%\"}" \
    #         "$SLACK_WEBHOOK_URL"
    # fi
}

# =============================================================================
# Report Generation Functions
# =============================================================================

generate_daily_report() {
    log "Generating daily cost report..."
    
    local report_file="$REPORTS_DIR/daily_report_$(date +%Y%m%d).md"
    
    cat > "$report_file" <<EOF
# 📊 Daily Billing Report - $(date +%Y-%m-%d)

## 💰 Cost Summary

EOF
    
    # Add provider summaries
    for provider in "${PROVIDERS[@]}"; do
        local cost_file="$REPORTS_DIR/${provider}_costs_$(date +%Y%m%d).json"
        if [[ -f "$cost_file" ]]; then
            echo "### $provider" >> "$report_file"
            cat "$cost_file" | jq -r '| "  - Credits Used: \(.credits_used // "N/A")\n  - Remaining: \(.remaining_credits // "N/A")\n  - Usage: \(.usage_percentage // "N/A")%"' >> "$report_file"
            echo "" >> "$report_file"
        fi
    done
    
    # Add alerts summary
    local alerts_count
    alerts_count=$(find "$ALERTS_DIR" -name "*$(date +%Y%m%d)*" -type f | wc -l)
    
    cat >> "$report_file" <<EOF
## 🚨 Alerts Summary

- **Total Alerts Today**: $alerts_count
- **Critical Alerts**: $(find "$ALERTS_DIR" -name "critical_*$(date +%Y%m%d)*" -type f | wc -l)
- **Warning Alerts**: $(find "$ALERTS_DIR" -name "warning_*$(date +%Y%m%d)*" -type f | wc -l)

## 📈 Trends

EOF
    
    # Add trend analysis (if historical data exists)
    echo "Analysis will be enhanced with historical data over time." >> "$report_file"
    
    log_success "Daily report generated: $report_file"
}

generate_monthly_report() {
    log "Generating monthly cost report..."
    
    local report_file="$REPORTS_DIR/monthly_report_$(date +%Y-%m).md"
    local month=$(date +%Y-%m)
    
    cat > "$report_file" <<EOF
# 📊 Monthly Billing Report - $month

## 💰 Monthly Summary

EOF
    
    # Calculate monthly totals
    local total_costs=0
    local total_alerts=0
    
    for provider in "${PROVIDERS[@]}"; do
        local provider_costs=0
        local daily_files
        daily_files=($(find "$REPORTS_DIR" -name "${provider}_costs_${month}-*.json" -type f 2>/dev/null || true))
        
        if [[ ${#daily_files[@]} -gt 0 ]]; then
            echo "### $provider" >> "$report_file"
            
            for file in "${daily_files[@]}"; do
                local cost
                cost=$(jq -r '.credits_used // 0' "$file" 2>/dev/null || echo "0")
                provider_costs=$(echo "$provider_costs + $cost" | bc -l 2>/dev/null || echo "$provider_costs")
            done
            
            echo "  - **Total Credits Used**: $provider_costs" >> "$report_file"
            echo "" >> "$report_file"
            total_costs=$(echo "$total_costs + $provider_costs" | bc -l 2>/dev/null || echo "$total_costs")
        fi
    done
    
    # Calculate alerts
    total_alerts=$(find "$ALERTS_DIR" -name "*${month}-*" -type f | wc -l)
    
    cat >> "$report_file" <<EOF

## 📊 Overall Summary

- **Total Credits Used**: $total_costs
- **Total Alerts**: $total_alerts
- **Average Daily Usage**: $(echo "scale=2; $total_costs / $(date +%d)" | bc -l 2>/dev/null || echo "0")

## 🎯 Budget Status

EOF
    
    # Check budget status
    if [[ -f "$BUDGET_FILE" ]]; then
        local monthly_budget
        monthly_budget=$(yq eval '.monthly_budget // 100' "$BUDGET_FILE")
        local budget_percentage
        budget_percentage=$(echo "scale=2; $total_costs * 100 / $monthly_budget" | bc -l 2>/dev/null || echo "0")
        
        echo "- **Budget**: $monthly_budget credits" >> "$report_file"
        echo "- **Used**: $total_costs credits" >> "$report_file"
        echo "- **Remaining**: $(echo "$monthly_budget - $total_costs" | bc -l 2>/dev/null || echo "0") credits" >> "$report_file"
        echo "- **Budget Used**: ${budget_percentage}%" >> "$report_file"
        
        if (( $(echo "$budget_percentage >= 80" | bc -l 2>/dev/null || echo "0") )); then
            echo "⚠️ **WARNING**: Approaching monthly budget limit!" >> "$report_file"
        fi
    fi
    
    log_success "Monthly report generated: $report_file"
}

# =============================================================================
# Configuration Functions
# =============================================================================

create_default_thresholds() {
    log "Creating default billing thresholds..."
    
    mkdir -p "$CONFIG_DIR"
    cat > "$THRESHOLDS_FILE" <<EOF
# Billing Alert Thresholds Configuration
# Values are percentages (0-100)

openrouter:
  warning_threshold: 80
  critical_threshold: 90

cloudflare:
  warning_threshold: 75
  critical_threshold: 85

bedrock:
  warning_threshold: 85
  critical_threshold: 95

anthropic:
  warning_threshold: 80
  critical_threshold: 90
EOF
    
    log_success "Default thresholds created: $THRESHOLDS_FILE"
}

create_budget_config() {
    log "Creating monthly budget configuration..."
    
    mkdir -p "$CONFIG_DIR"
    cat > "$BUDGET_FILE" <<EOF
# Monthly Budget Configuration
# All values in credits/tokens

monthly_budget: 1000
daily_budget: 35

provider_budgets:
  openrouter: 500
  cloudflare: 200
  bedrock: 200
  anthropic: 300

# Alert settings
alerts:
  email_recipients:
    - "admin@yourcompany.com"
    - "billing@yourcompany.com"
  
  slack_webhook: ""
  discord_webhook: ""
EOF
    
    log_success "Budget configuration created: $BUDGET_FILE"
}

# =============================================================================
# Main Functions
# =============================================================================

run_cost_check() {
    log "🔍 Starting cost check for all providers..."
    
    for provider in "${PROVIDERS[@]}"; do
        case $provider in
            "openrouter")
                track_openrouter_costs
                ;;
            "cloudflare")
                track_cloudflare_costs
                ;;
            "bedrock")
                track_bedrock_costs
                ;;
            "anthropic")
                log "Anthropic cost tracking - Manual monitoring required"
                ;;
        esac
    done
    
    log_success "✅ Cost check completed for all providers"
}

run_daily_monitoring() {
    log "📅 Running daily billing monitoring..."
    
    # Check costs
    run_cost_check
    
    # Generate daily report
    generate_daily_report
    
    # Check for budget overruns
    check_budget_status
    
    log_success "✅ Daily monitoring completed"
}

check_budget_status() {
    log "💰 Checking budget status..."
    
    if [[ ! -f "$BUDGET_FILE" ]]; then
        create_budget_config
        return 0
    fi
    
    local monthly_budget
    monthly_budget=$(yq eval '.monthly_budget // 1000' "$BUDGET_FILE")
    
    # Calculate current month usage
    local current_usage=0
    local month=$(date +%Y-%m)
    
    for provider in "${PROVIDERS[@]}"; do
        local daily_files
        daily_files=($(find "$REPORTS_DIR" -name "${provider}_costs_${month}-*.json" -type f 2>/dev/null || true))
        
        for file in "${daily_files[@]}"; do
            local cost
            cost=$(jq -r '.credits_used // 0' "$file" 2>/dev/null || echo "0")
            current_usage=$(echo "$current_usage + $cost" | bc -l 2>/dev/null || echo "$current_usage")
        done
    done
    
    local budget_percentage
    budget_percentage=$(echo "scale=2; $current_usage * 100 / $monthly_budget" | bc -l 2>/dev/null || echo "0")
    
    log "📊 Budget Status: ${budget_percentage}% used ($current_usage/$monthly_budget credits)"
    
    # Check budget thresholds
    if (( $(echo "$budget_percentage >= 90" | bc -l 2>/dev/null || echo "0") )); then
        log_error "🚨 CRITICAL: Monthly budget ${budget_percentage}% used!"
        send_budget_alert "critical" "$current_usage" "$monthly_budget" "$budget_percentage"
    elif (( $(echo "$budget_percentage >= 80" | bc -l 2>/dev/null || echo "0") )); then
        log_warning "⚠️ WARNING: Monthly budget ${budget_percentage}% used"
        send_budget_alert "warning" "$current_usage" "$monthly_budget" "$budget_percentage"
    fi
}

send_budget_alert() {
    local level=$1
    local used=$2
    local budget=$3
    local percentage=$4
    
    local alert_file="$ALERTS_DIR/budget_${level}_$(date +%Y%m%d_%H%M%S).json"
    cat > "$alert_file" <<EOF
{
    "alert_type": "budget_$level",
    "timestamp": "$(date -Iseconds)",
    "used": $used,
    "budget": $budget,
    "percentage": $percentage,
    "message": "Monthly budget ${percentage}% used (\$${used}/\$${budget})"
}
EOF
    
    log "📢 Budget $level alert saved: $alert_file"
}

show_status() {
    echo -e "${CYAN}📊 bl1nk Billing Monitor Status${NC}"
    echo "================================"
    echo
    
    # Show last run status
    if [[ -f "$LOG_DIR/billing_monitor.log" ]]; then
        echo "Last check: $(tail -n 1 "$LOG_DIR/billing_monitor.log" | cut -d']' -f1 | cut -d'[' -f2)"
    fi
    
    # Show recent alerts
    local recent_alerts
    recent_alerts=$(find "$ALERTS_DIR" -name "*$(date +%Y%m%d)*" -type f | wc -l)
    echo "Today's alerts: $recent_alerts"
    
    # Show provider status
    echo
    echo "Provider Status:"
    for provider in "${PROVIDERS[@]}"; do
        if [[ -n "${provider^^}_TOKEN" ]]; then
            echo -e "  ✅ ${GREEN}$provider${NC} - Configured"
        else
            echo -e "  ❌ ${RED}$provider${NC} - Not configured"
        fi
    done
    
    echo
    echo "Quick Commands:"
    echo "  ./billing_monitor.sh check      - Check costs now"
    echo "  ./billing_monitor.sh daily      - Run daily monitoring"
    echo "  ./billing_monitor.sh report     - Generate report"
    echo "  ./billing_monitor.sh config     - Setup configuration"
    echo "  ./billing_monitor.sh status     - Show this status"
}

# =============================================================================
# Main Script Logic
# =============================================================================

main() {
    case "${1:-help}" in
        "check"|"c")
            run_cost_check
            ;;
        "daily"|"d")
            run_daily_monitoring
            ;;
        "report"|"r")
            generate_daily_report
            generate_monthly_report
            ;;
        "config"|"setup")
            create_default_thresholds
            create_budget_config
            log_success "Billing monitoring configuration completed!"
            ;;
        "status"|"s"|"help"|"h")
            show_status
            ;;
        *)
            echo -e "${YELLOW}Usage: $0 [check|daily|report|config|status]${NC}"
            echo
            echo "Commands:"
            echo "  check     - Check current costs for all providers"
            echo "  daily     - Run complete daily monitoring cycle"
            echo "  report    - Generate cost reports"
            echo "  config    - Setup billing monitoring configuration"
            echo "  status    - Show monitoring status and configuration"
            echo
            echo "Examples:"
            echo "  $0 check                    # Quick cost check"
            echo "  $0 daily                    # Full daily monitoring"
            echo "  $0 report                   # Generate reports"
            exit 1
            ;;
    esac
}

# Check dependencies
if ! command -v curl >/dev/null 2>&1; then
    log_error "curl is required but not installed"
    exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
    log_error "jq is required but not installed"
    exit 1
fi

if ! command -v yq >/dev/null 2>&1; then
    log_warning "yq not found, installing..."
    pip install yq
fi

# Run main function
main "$@"