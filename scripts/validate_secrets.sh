#!/bin/bash

# =============================================================================
# bl1nk-agent-builder Secret Validation Script
# =============================================================================
# สคริปสำหรับตรวจสอบและ validate API keys และ secrets ที่จำเป็นสำหรับโปรเจ็ค
# Usage: ./scripts/validate_secrets.sh
# =============================================================================

set -euo pipefail

# Load values from .env (without sourcing/executing it).
# This lets the script validate secrets right after copying `config/env.example`
# without requiring `export`/`source` in the current shell.
trim() {
    local s="$1"
    s="${s#"${s%%[![:space:]]*}"}"
    s="${s%"${s##*[![:space:]]}"}"
    printf '%s' "$s"
}

declare -A ENV_FILE_VALUES=()

load_env_file() {
    local env_path="${1:-.env}"
    [[ -f "$env_path" ]] || return 0

    while IFS= read -r raw_line || [[ -n "$raw_line" ]]; do
        local line="${raw_line%$'\r'}"
        line="$(trim "$line")"

        [[ -z "$line" ]] && continue
        [[ "${line:0:1}" == "#" ]] && continue

        if [[ "$line" == export\ * ]]; then
            line="${line#export }"
        fi

        [[ "$line" == *"="* ]] || continue

        local key="${line%%=*}"
        local value="${line#*=}"
        key="$(trim "$key")"
        value="$(trim "$value")"

        [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue

        # Strip inline comments for unquoted values.
        if [[ "$value" != \"*\" && "$value" != \'*\' ]]; then
            value="${value%%#*}"
            value="$(trim "$value")"
        fi

        # Strip a single pair of surrounding quotes.
        if [[ "$value" =~ ^\".*\"$ ]]; then
            value="${value:1:-1}"
        elif [[ "$value" =~ ^\'.*\'$ ]]; then
            value="${value:1:-1}"
        fi

        ENV_FILE_VALUES["$key"]="$value"
    done < "$env_path"
}

get_secret_value() {
    local var_name="$1"
    if [[ -n "${!var_name:-}" ]]; then
        printf '%s' "${!var_name}"
        return 0
    fi
    if [[ -n "${ENV_FILE_VALUES[$var_name]+x}" ]]; then
        printf '%s' "${ENV_FILE_VALUES[$var_name]}"
        return 0
    fi
    return 1
}

is_placeholder_value() {
    local var_name="$1"
    local var_value="$2"

    # Generic template placeholders used across env.example
    if [[ "$var_value" == your-* ]] || [[ "$var_value" == *"-your-"* ]] || [[ "$var_value" == "..." ]]; then
        return 0
    fi

    case "$var_name" in
        DB_DSN)
            [[ "$var_value" == postgresql://user:password@* ]] || [[ "$var_value" == *"neon-host.neon.tech"* ]]
            ;;
        UPSTASH_REDISURL)
            [[ "$var_value" == rediss://:token@* ]] || [[ "$var_value" == *"global.upstash.io"* ]]
            ;;
        OPENROUTER_TOKEN)
            [[ "$var_value" == "your-openrouter-api-token" ]]
            ;;
        CLOUDFLARE_API_TOKEN)
            [[ "$var_value" == "your-cloudflare-api-token" ]]
            ;;
        BEDROCK_TOKEN)
            [[ "$var_value" == "your-aws-bedrock-token" ]]
            ;;
        JWT_SECRET)
            [[ "$var_value" == "your-super-secret-jwt-key-change-this-in-production" ]]
            ;;
        ENCRYPTION_KEY)
            [[ "$var_value" == "your-32-character-encryption-key" ]]
            ;;
        ADMIN_API_KEY)
            [[ "$var_value" == "your-admin-api-key-for-sensitive-operations" ]]
            ;;
        *)
            return 1
            ;;
    esac
}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counter for issues
TOTAL_ISSUES=0
REQUIRED_MISSING=0
OPTIONAL_MISSING=0

echo -e "${BLUE}🔍 bl1nk-agent-builder Secret Validation${NC}"
echo "=================================================="
echo ""

# Load .env values once (if present)
load_env_file ".env"

# Function to check if a variable is set and not empty
check_secret() {
    local var_name="$1"
    local var_value=""
    local is_required="${2:-true}"
    local description="$3"

    var_value="$(get_secret_value "$var_name" || true)"
    
    if [[ -z "$var_value" ]]; then
        if [[ "$is_required" == "true" ]]; then
            echo -e "${RED}❌ $var_name${NC} - จำเป็น: $description"
            REQUIRED_MISSING=$((REQUIRED_MISSING + 1))
            TOTAL_ISSUES=$((TOTAL_ISSUES + 1))
        else
            echo -e "${YELLOW}⚠️  $var_name${NC} - ตัวเลือก: $description"
            OPTIONAL_MISSING=$((OPTIONAL_MISSING + 1))
        fi
    elif is_placeholder_value "$var_name" "$var_value"; then
        if [[ "$is_required" == "true" ]]; then
            echo -e "${RED}❌ $var_name${NC} - จำเป็น: $description (ยังเป็นค่า placeholder จาก template)"
            REQUIRED_MISSING=$((REQUIRED_MISSING + 1))
            TOTAL_ISSUES=$((TOTAL_ISSUES + 1))
        else
            echo -e "${YELLOW}⚠️  $var_name${NC} - ตัวเลือก: $description (ยังเป็นค่า placeholder จาก template)"
            OPTIONAL_MISSING=$((OPTIONAL_MISSING + 1))
        fi
    else
        echo -e "${GREEN}✅ $var_name${NC} - ตั้งค่าแล้ว: $description"
    fi
}

# Function to validate API key format
validate_api_format() {
    local var_name="$1"
    local var_value=""
    local pattern="$2"
    local description="$3"

    var_value="$(get_secret_value "$var_name" || true)"
    
    if [[ -n "$var_value" ]]; then
        if [[ "$var_value" =~ $pattern ]]; then
            echo -e "${GREEN}  ✓ Format ถูกต้อง${NC}"
        else
            echo -e "${RED}  ❌ Format ไม่ถูกต้อง - ควรเป็น: $description${NC}"
            TOTAL_ISSUES=$((TOTAL_ISSUES + 1))
        fi
    fi
}

# Function to generate secret links
generate_secret_links() {
    echo ""
    echo -e "${BLUE}🔗 ลิ้งไปสำหรับขอ API Keys:${NC}"
    echo "=================================================="
    echo ""
    echo "📊 **Database & Storage:**"
    echo "• Neon Postgres: https://neon.tech/"
    echo "• Upstash Redis: https://upstash.com/"
    echo "• Cloudflare R2: https://dash.cloudflare.com/"
    echo ""
    echo "🤖 **LLM Providers:**"
    echo "• OpenRouter: https://openrouter.ai/keys"
    echo "• Cloudflare Gateway: https://dash.cloudflare.com/"
    echo "• AWS Bedrock: https://console.aws.amazon.com/bedrock/"
    echo ""
    echo "🔗 **Integrations:**"
    echo "• Slack App: https://api.slack.com/apps"
    echo "• GitHub App: https://github.com/settings/apps/new"
    echo "• Poe: https://poe.com/"
    echo "• Clerk: https://dashboard.clerk.com/"
    echo ""
    echo "🔒 **Security & Monitoring:**"
    echo "• Sentry: https://sentry.io/"
    echo "• OpenTelemetry: https://opentelemetry.io/"
}

# Check required environment variables
echo -e "${BLUE}🔐 ตรวจสอบ Environment Variables${NC}"
echo "=================================================="

# Database Configuration
echo -e "\n${YELLOW}📊 Database Configuration${NC}"
check_secret "DB_DSN" "true" "Neon Postgres connection string"
check_secret "UPSTASH_REDISURL" "true" "Upstash Redis connection"

# LLM Providers
echo -e "\n${YELLOW}🤖 LLM Providers${NC}"
check_secret "OPENROUTER_TOKEN" "true" "OpenRouter API token"
check_secret "CLOUDFLARE_API_TOKEN" "false" "Cloudflare Gateway API token"
check_secret "BEDROCK_TOKEN" "false" "AWS Bedrock credentials"

# Security
echo -e "\n${YELLOW}🔒 Security${NC}"
check_secret "JWT_SECRET" "true" "JWT signing secret"
check_secret "ENCRYPTION_KEY" "true" "AES-256 encryption key (32 chars)"
check_secret "ADMIN_API_KEY" "true" "Admin API key for sensitive operations"

# Storage
echo -e "\n${YELLOW}💾 Object Storage${NC}"
check_secret "R2_ACCESS_KEY" "false" "Cloudflare R2 access key"
check_secret "R2_SECRET_KEY" "false" "Cloudflare R2 secret key"

# Integrations (Optional but recommended)
echo -e "\n${YELLOW}🔗 Integrations${NC}"
check_secret "SLACK_SIGNING_SECRET" "false" "Slack app signing secret"
check_secret "SLACK_BOT_TOKEN" "false" "Slack bot token"
check_secret "GITHUB_WEBHOOK_SECRET" "false" "GitHub webhook secret"
check_secret "POE_WEBHOOK_SECRET" "false" "Poe webhook secret"
check_secret "CLERK_SECRET_KEY" "false" "Clerk authentication key"

# Monitoring
echo -e "\n${YELLOW}📊 Monitoring & Observability${NC}"
check_secret "SENTRY_DSN" "false" "Sentry error tracking DSN"
check_secret "OTEL_EXPORTER_OTLP_ENDPOINT" "false" "OpenTelemetry endpoint"

# Validate API key formats
echo -e "\n${BLUE}🔍 ตรวจสอบ Format ของ API Keys${NC}"
echo "=================================================="

# OpenRouter token format (usually starts with sk-or-)
validate_api_format "OPENROUTER_TOKEN" "^sk-or-" "OpenRouter token ควรเริ่มต้นด้วย sk-or-"

# JWT secret length
JWT_SECRET_VALUE="$(get_secret_value "JWT_SECRET" || true)"
if [[ -n "$JWT_SECRET_VALUE" ]]; then
    if [[ ${#JWT_SECRET_VALUE} -ge 32 ]]; then
        echo -e "${GREEN}  ✓ JWT Secret length ถูกต้อง (${#JWT_SECRET_VALUE} chars)${NC}"
    else
        echo -e "${RED}  ❌ JWT Secret ควรมีอย่างน้อย 32 ตัวอักษร${NC}"
        TOTAL_ISSUES=$((TOTAL_ISSUES + 1))
    fi
fi

# Encryption key length
ENCRYPTION_KEY_VALUE="$(get_secret_value "ENCRYPTION_KEY" || true)"
if [[ -n "$ENCRYPTION_KEY_VALUE" ]]; then
    if [[ ${#ENCRYPTION_KEY_VALUE} -eq 32 ]]; then
        echo -e "${GREEN}  ✓ Encryption Key length ถูกต้อง (32 chars)${NC}"
    else
        echo -e "${RED}  ❌ Encryption Key ต้องมี 32 ตัวอักษร${NC}"
        TOTAL_ISSUES=$((TOTAL_ISSUES + 1))
    fi
fi

# Generate links for obtaining secrets
generate_secret_links

# Network connectivity checks (optional)
echo -e "\n${BLUE}🌐 ตรวจสอบการเชื่อมต่อ Network${NC}"
echo "=================================================="

# Check connectivity to external services
check_connectivity() {
    local service_name="$1"
    local url="$2"
    
    if curl -s --max-time 5 "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name${NC} - เชื่อมต่อได้"
    else
        echo -e "${RED}❌ $service_name${NC} - ไม่สามารถเชื่อมต่อได้"
        TOTAL_ISSUES=$((TOTAL_ISSUES + 1))
    fi
}

# Check external services
check_connectivity "OpenRouter" "https://openrouter.ai/api/v1"
check_connectivity "Cloudflare Gateway" "https://gateway.ai.cloudflare.com"
check_connectivity "Neon Postgres" "https://neon.tech"

# Generate .env template if not exists
echo -e "\n${BLUE}📝 สร้าง .env template${NC}"
echo "=================================================="

if [[ ! -f ".env" ]]; then
    cp config/env.example .env
    echo -e "${GREEN}✅ สร้างไฟล์ .env จาก template แล้ว${NC}"
    echo -e "${YELLOW}⚠️  กรุณาแก้ไขไฟล์ .env ด้วยค่าจริงของคุณ${NC}"
else
    echo -e "${YELLOW}⚠️  ไฟล์ .env มีอยู่แล้ว${NC}"
fi

# Summary
echo ""
echo -e "${BLUE}📊 สรุปผลการตรวจสอบ${NC}"
echo "=================================================="
echo -e "ปัญหาที่จำเป็นต้องแก้ไข: ${RED}$REQUIRED_MISSING${NC}"
echo -e "การตั้งค่าที่แนะนำ: ${YELLOW}$OPTIONAL_MISSING${NC}"
echo -e "รวมปัญหาทั้งหมด: ${RED}$TOTAL_ISSUES${NC}"

if [[ $TOTAL_ISSUES -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}🎉 ยินดีด้วย! การตั้งค่าทั้งหมดถูกต้อง${NC}"
    echo -e "${GREEN}✅ คุณพร้อมที่จะเริ่มใช้งาน bl1nk-agent-builder แล้ว${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}⚠️  กรุณาแก้ไขปัญหาที่ระบุข้างต้นก่อนเริ่มใช้งาน${NC}"
    echo ""
    echo -e "${BLUE}💡 เคล็ดลับ:${NC}"
    echo "• ใช้ QUICK_START_GUIDE.md สำหรับคำแนะนำเพิ่มเติม"
    echo "• ดูลิ้งด้านบนเพื่อขอ API keys จาก providers"
    echo "• ตรวจสอบ documentation ใน docs/ directory"
    exit 1
fi
