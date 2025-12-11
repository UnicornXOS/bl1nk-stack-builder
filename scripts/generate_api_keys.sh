#!/bin/bash

# =============================================================================
# API Key Generator Helper
# =============================================================================
# สคริปสำหรับสร้าง API key templates และ links
# Usage: ./scripts/generate_api_keys.sh
# =============================================================================

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🔑 bl1nk-agent-builder API Key Generator${NC}"
echo "=============================================="

# Function to create API key template
create_api_template() {
    local filename="$1"
    local title="$2"
    
    cat > "$filename" << EOF
# =============================================================================
# $title
# =============================================================================

EOF

    case "$filename" in
        "OPENROUTER.md")
            cat >> "$filename" << 'EOF'
## OpenRouter API Key Setup

### Steps:
1. Go to [OpenRouter](https://openrouter.ai/)
2. Sign up / Log in
3. Navigate to [API Keys](https://openrouter.ai/keys)
4. Create new API key
5. Copy the key (starts with \`sk-or-\`)

### Your API Key:
\`\`\`
OPENROUTER_TOKEN=sk-or-your-key-here
\`\`\`

### Important Notes:
- Keep your API key secure
- Never commit it to version control
- Monitor usage in OpenRouter dashboard
EOF
            ;;
        "CLOUDFLARE.md")
            cat >> "$filename" << 'EOF'
## Cloudflare Gateway Setup

### Steps:
1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Navigate to **AI Gateway**
3. Create new Gateway
4. Go to Settings → API Tokens
5. Create new API Token with AI Gateway permissions

### Your API Token:
\`\`\`
CLOUDFLARE_API_TOKEN=your-token-here
CLOUDFLARE_ACCOUNT_ID=your-account-id
\`\`\`
EOF
            ;;
        "DATABASE.md")
            cat >> "$filename" << 'EOF'
## Database Setup

### Neon Postgres:
1. Go to [Neon](https://neon.tech/)
2. Sign up / Log in
3. Create new project
4. Get connection string from Settings → Database

### Your Connection String:
\`\`\`
DB_DSN=postgresql://user:password@ep-example.us-east-1.aws.neon.tech:5432/bl1nk
\`\`\`

### Upstash Redis:
1. Go to [Upstash](https://upstash.com/)
2. Sign up / Log in
3. Create Redis database
4. Copy REST URL

### Your Redis URL:
\`\`\`
UPSTASH_REDISURL=rediss://:abc123@us1-some-id.upstash.io:6379
\`\`\`
EOF
            ;;
        "SECURITY.md")
            cat >> "$filename" << 'EOF'
## Security Configuration

### Generate Secure Keys:

#### JWT Secret (minimum 32 characters):
\`\`\`
JWT_SECRET=$(openssl rand -base64 32)
\`\`\`

#### Encryption Key (exactly 32 characters):
\`\`\`
ENCRYPTION_KEY=$(openssl rand -hex 16)
\`\`\`

#### Admin API Key:
\`\`\`
ADMIN_API_KEY=$(openssl rand -base64 24)
\`\`\`

### Generate All Keys at Once:
\`\`\`bash
# JWT Secret
JWT_SECRET=$(openssl rand -base64 32)

# Encryption Key
ENCRYPTION_KEY=$(openssl rand -hex 16)

# Admin API Key
ADMIN_API_KEY=$(openssl rand -base64 24)

echo "JWT_SECRET=$JWT_SECRET"
echo "ENCRYPTION_KEY=$ENCRYPTION_KEY"
echo "ADMIN_API_KEY=$ADMIN_API_KEY"
\`\`\`
EOF
            ;;
    esac
}

# Create API key template files
echo -e "${YELLOW}📝 Creating API key templates...${NC}"

create_api_template "OPENROUTER.md" "OpenRouter API Key Setup"
create_api_template "CLOUDFLARE.md" "Cloudflare Gateway Setup"
create_api_template "DATABASE.md" "Database Configuration"
create_api_template "SECURITY.md" "Security Configuration"

echo -e "${GREEN}✅ Created template files:${NC}"
echo "  - OPENROUTER.md"
echo "  - CLOUDFLARE.md"
echo "  - DATABASE.md"
echo "  - SECURITY.md"

# Create comprehensive API keys guide
cat > "API_KEYS_GUIDE.md" << 'EOF'
# 🔑 Complete API Keys Setup Guide

## 📋 Required API Keys

### 1. Database & Storage (Required)
- **Neon Postgres**: Database connection
- **Upstash Redis**: Cache and queue management

### 2. LLM Providers (Required - at least one)
- **OpenRouter**: Primary LLM provider
- **Cloudflare Gateway**: Secondary LLM provider  
- **AWS Bedrock**: Fallback LLM provider

### 3. Security (Required)
- **JWT Secret**: For token signing
- **Encryption Key**: For data encryption
- **Admin API Key**: For administrative operations

## 🚀 Quick Setup Links

### Primary Providers
| Service | Sign Up | API Keys | Dashboard |
|---------|---------|----------|-----------|
| [Neon](https://neon.tech/) | [Sign Up](https://neon.tech/) | [Database](https://neon.tech/) | [Dashboard](https://neon.tech/dashboard) |
| [Upstash](https://upstash.com/) | [Sign Up](https://upstash.com/) | [Redis](https://upstash.com/) | [Dashboard](https://upstash.com/dashboard) |
| [OpenRouter](https://openrouter.ai/) | [Sign Up](https://openrouter.ai/) | [API Keys](https://openrouter.ai/keys) | [Dashboard](https://openrouter.ai/dashboard) |

### Secondary Providers
| Service | Sign Up | API Keys | Dashboard |
|---------|---------|----------|-----------|
| [Cloudflare](https://cloudflare.com/) | [Sign Up](https://cloudflare.com/) | [AI Gateway](https://dash.cloudflare.com/) | [Dashboard](https://dash.cloudflare.com/) |
| [AWS](https://aws.amazon.com/) | [Sign Up](https://aws.amazon.com/) | [Bedrock](https://console.aws.amazon.com/bedrock/) | [Console](https://console.aws.amazon.com/) |

### Integration Services
| Service | Sign Up | Setup | Dashboard |
|---------|---------|-------|-----------|
| [Slack](https://slack.com/) | [Create App](https://api.slack.com/apps) | [OAuth](https://api.slack.com/authentication/oauth-v2) | [Dashboard](https://api.slack.com/apps) |
| [GitHub](https://github.com/) | [Create App](https://github.com/settings/apps/new) | [Webhooks](https://docs.github.com/en/developers/webhooks-and-events/webhooks) | [Settings](https://github.com/settings/apps) |
| [Clerk](https://clerk.com/) | [Sign Up](https://clerk.com/) | [API Keys](https://dashboard.clerk.com/) | [Dashboard](https://dashboard.clerk.com/) |

## ⚡ Quick Start Commands

### Generate Security Keys
```bash
# Generate JWT Secret
JWT_SECRET=$(openssl rand -base64 32)

# Generate Encryption Key
ENCRYPTION_KEY=$(openssl rand -hex 16)

# Generate Admin API Key
ADMIN_API_KEY=$(openssl rand -base64 24)

echo "JWT_SECRET=$JWT_SECRET"
echo "ENCRYPTION_KEY=$ENCRYPTION_KEY"
echo "ADMIN_API_KEY=$ADMIN_API_KEY"
```

### Copy Template and Fill
```bash
# Copy environment template
cp config/env.example .env

# Edit with your values
nano .env
```

### Validate Configuration
```bash
# Run validation script
./scripts/validate_secrets.sh
```

## 📚 Detailed Guides

See individual guide files for step-by-step instructions:
- `OPENROUTER.md` - OpenRouter API setup
- `CLOUDFLARE.md` - Cloudflare Gateway setup  
- `DATABASE.md` - Database configuration
- `SECURITY.md` - Security key generation

## ✅ Checklist

Before proceeding:
- [ ] Created accounts with required providers
- [ ] Generated API keys for all required services
- [ ] Updated .env files with real values
- [ ] Ran validation script successfully
- [ ] Tested database and Redis connections
- [ ] Verified LLM provider access

For detailed instructions, see `QUICK_START_GUIDE.md`.
EOF

echo ""
echo -e "${GREEN}📚 Created comprehensive guide: API_KEYS_GUIDE.md${NC}"

echo ""
echo -e "${BLUE}🎯 Next Steps:${NC}"
echo "1. อ่าน API_KEYS_GUIDE.md สำหรับภาพรวม"
echo "2. อ่านไฟล์ template แต่ละตัวสำหรับขั้นตอนที่ละเอียด"
echo "3. สร้าง accounts และ API keys"
echo "4. อัปเดต .env files"
echo "5. รัน ./scripts/validate_secrets.sh เพื่อตรวจสอบ"
echo ""
echo -e "${GREEN}✅ พร้อมเริ่มต้นแล้ว!${NC}"