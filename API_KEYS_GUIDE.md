---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: "00000000000000000000000000000000"
    PropagateID: "00000000000000000000000000000000"
    ReservedCode1: 304502201abae0112f7dc5a5f3df2e1ea6b96c673cbc00165027eed91ab95994c19599d3022100cb16b267fe253e8c041916b4746a72640be64d59cff9deec41263bab44d0c194
    ReservedCode2: 30460221008baffb51478649b9f6be4c8ab854de3db4f4da452df3f492dd9c7d3f4c0f1f10022100d4e2d546c2e9286146f2a4506b04c3461db15d35c364444c7734ae6d7e61c49e
---

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
