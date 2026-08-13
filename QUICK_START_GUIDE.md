---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: "00000000000000000000000000000000"
    PropagateID: "00000000000000000000000000000000"
    ReservedCode1: 3045022070479b0f97b6339a232af25027d7480164a585c85e6736b6f6e1b5b3c0b093a2022100cfa0b128a31e2492955761cd2c64b6bf8b67d1ab7a715c34afc496080cea1896
    ReservedCode2: 304502202bc09ec492c13ddb216001b4d531a0ee97f6545545d40f98f506910672995921022100de32b8d8dfab225f6510643cb0f8e370525e82c63d8122b618fa8de23c2d0d2c
---

# 🚀 bl1nk-agent-builder Quick Start Guide

## คู่มือเริ่มต้นใช้งาน bl1nk-agent-builder อย่างละเอียด

### 📋 สารบัญ

1. [การเตรียมความพร้อม](#การเตรียมความพร้อม)
2. [การติดตั้งและตั้งค่า](#การติดตั้งและตั้งค่า)
3. [การขอ API Keys](#การขอ-api-keys)
4. [การตรวจสอบการตั้งค่า](#การตรวจสอบการตั้งค่า)
5. [การเริ่มต้นใช้งาน](#การเริ่มต้นใช้งาน)
6. [การแก้ไขปัญหา](#การแก้ไขปัญหา)

---

## 🎯 การเตรียมความพร้อม

### ข้อกำหนดระบบ

**Software ที่จำเป็น:**
- **Python 3.11+** (รองรับ full compatibility)
- **Node.js 18+** (สำหรับ Cloudflare Worker)
- **Git** (สำหรับ version control)
- **Docker** (แนะนำสำหรับ development)

**Accounts ที่จำเป็น:**
- 🗄️ **Neon Postgres** (ฐานข้อมูล)
- 🚀 **Upstash Redis** (cache และ queue)
- 🤖 **OpenRouter** (LLM provider หลัก)
- ☁️ **Cloudflare** (gateway และ storage)
- 🐙 **GitHub** (สำหรับ CI/CD)

**Accounts ที่แนะนำ (Optional):**
- 🤖 **AWS Bedrock** (LLM fallback provider)
- 📊 **Sentry** (error monitoring)
- 🔐 **Clerk** (authentication service)

---

## ⚙️ การติดตั้งและตั้งค่า

### 1. Clone Repository

```bash
# Clone โปรเจ็ค
git clone <your-repository-url>
cd bl1nk-agent-builder

# ตรวจสอบโครงสร้างไฟล์
ls -la
```

### 2. รัน Bootstrap Script

```bash
# ให้สิทธิ์ execute สำหรับสคริปต์
chmod +x scripts/*.sh

# Windows PowerShell: ไม่มีคำสั่ง `chmod`
# - แนะนำให้รันใน Git Bash หรือ
# - เรียกสคริปต์ผ่าน bash โดยตรง เช่น `bash scripts/bootstrap.sh development`

# รัน bootstrap สำหรับ development environment
./scripts/bootstrap.sh development

# หรือสำหรับ production
./scripts/bootstrap.sh production
```

### 3. คัดลอก Environment Template

```bash
# คัดลอก template
cp config/env.example .env

# คัดลอกสำหรับ worker app
cp config/env.example apps/worker/.env
```

---

## 🔑 การขอ API Keys

### 🗄️ Database & Storage

#### Neon Postgres
1. ไปที่ [neon.tech](https://neon.tech/)
2. สมัครสมาชิก (ใช้ GitHub ได้)
3. สร้าง Project ใหม่
4. คัดลอก connection string:
   ```
   postgresql://user:password@ep-example.us-east-1.aws.neon.tech:5432/bl1nk
   ```

#### Upstash Redis
1. ไปที่ [upstash.com](https://upstash.com/)
2. สมัครสมาชิก
3. สร้าง Redis Database
4. คัดลอก REST URL:
   ```
   rediss://:abc123@us1-some-id.upstash.io:6379
   ```

### 🤖 LLM Providers (จำเป็นต้องมีอย่างน้อย 1 ตัว)

#### OpenRouter (แนะนำเป็นตัวแรก)
1. ไปที่ [openrouter.ai](https://openrouter.ai/)
2. สมัครสมาชิก
3. ไปที่ [API Keys](https://openrouter.ai/keys)
4. สร้าง API Key ใหม่
5. คัดลอก token (เริ่มต้นด้วย `sk-or-`)

#### Cloudflare Gateway
1. ไปที่ [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. ไปที่ **AI Gateway**
3. สร้าง Gateway ใหม่
4. ใน Settings → API Token สร้าง token ใหม่
5. คัดลอก API Token

#### AWS Bedrock
1. ไปที่ [AWS Console](https://console.aws.amazon.com/)
2. ไปที่ **Bedrock**
3. เปิดใช้งาน Bedrock ใน region ที่ต้องการ
4. สร้าง IAM User สำหรับ Bedrock
5. สร้าง Access Key และ Secret Key

### ☁️ Storage (Optional)

#### Cloudflare R2
1. ไปที่ [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. ไปที่ **R2 Object Storage**
3. สร้าง Bucket ใหม่
4. ไปที่ **Manage R2 API tokens**
5. สร้าง API token พร้อม permissions สำหรับ Read/Write

### 🔗 Integrations (Optional)

#### Slack App
1. ไปที่ [Slack API](https://api.slack.com/apps)
2. สร้าง App ใหม่
3. ใน **Basic Information**:
   - Copy **Client ID**, **Client Secret**
   - Copy **Signing Secret**
4. ใน **OAuth & Permissions**:
   - ติดตั้ง App ไปยัง Workspace
   - Copy **Bot User OAuth Token** (เริ่มต้นด้วย `xoxb-`)
   - Copy **App-Level Token** (เริ่มต้นด้วย `xapp-`)

#### GitHub App
1. ไปที่ GitHub Settings → **Developer settings** → **GitHub Apps**
2. สร้าง GitHub App ใหม่:
   - **Homepage URL**: ของคุณ
   - **Webhook URL**: `https://your-domain.com/webhook/github`
   - **Webhook Secret**: สร้างใหม่
3. สร้าง Private Key สำหรับ App
4. ติดตั้ง App ไปยัง Repository ที่ต้องการ

#### Clerk Authentication
1. ไปที่ [Clerk Dashboard](https://dashboard.clerk.com/)
2. สร้าง Application ใหม่
3. ใน **Configure** → **API Keys**:
   - Copy **Publishable key**
   - Copy **Secret key**
4. ใน **Configure** → **JWT Templates**:
   - สร้าง JWT Template
   - Copy **JWT Signing Key**

---

## ⚙️ การตั้งค่า Environment Variables

### ไฟล์ .env หลัก (Root Directory)

```bash
# =============================================================================
# DATABASE CONFIGURATION (จำเป็น)
# =============================================================================
DB_DSN=postgresql://user:password@ep-example.us-east-1.aws.neon.tech:5432/bl1nk

# =============================================================================
# REDIS CONFIGURATION (จำเป็น)
# =============================================================================
UPSTASH_REDISURL=rediss://:abc123@us1-some-id.upstash.io:6379

# =============================================================================
# LLM PROVIDERS (จำเป็นอย่างน้อย 1 ตัว)
# =============================================================================
OPENROUTER_TOKEN=sk-or-your-openrouter-token

# Optional providers
CLOUDFLARE_API_TOKEN=your-cloudflare-token
BEDROCK_TOKEN=your-aws-credentials

# =============================================================================
# SECURITY (จำเป็น)
# =============================================================================
JWT_SECRET=your-super-secret-jwt-key-minimum-32-characters
ENCRYPTION_KEY=your-32-character-encryption-key
ADMIN_API_KEY=your-admin-api-key

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================
ENVIRONMENT=development
DEBUG=true
FASTAPI_URL=http://localhost:8000
```

### ไฟล์ apps/worker/.env

```bash
# =============================================================================
# WORKER APPLICATION SETTINGS
# =============================================================================
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8000

# =============================================================================
# DATABASE
# =============================================================================
DATABASE_URL=postgresql://user:password@ep-example.us-east-1.aws.neon.tech:5432/bl1nk

# =============================================================================
# REDIS
# =============================================================================
REDIS_URL=rediss://:abc123@us1-some-id.upstash.io:6379

# =============================================================================
# LLM PROVIDERS
# =============================================================================
OPENROUTER_API_KEY=sk-or-your-openrouter-token
CLOUDFLARE_API_TOKEN=your-cloudflare-token
BEDROCK_REGION=us-east-1
BEDROCK_ACCESS_KEY_ID=your-access-key
BEDROCK_SECRET_ACCESS_KEY=your-secret-key

# =============================================================================
# SECURITY
# =============================================================================
JWT_SECRET_KEY=your-super-secret-jwt-key-minimum-32-characters
ENCRYPTION_KEY=your-32-character-encryption-key
ADMIN_API_KEY=your-admin-api-key
```

---

## 🔍 การตรวจสอบการตั้งค่า

### 1. รัน Secret Validation Script

```bash
# ตรวจสอบ API keys และ secrets
./scripts/validate_secrets.sh
```

**ผลลัพธ์ที่คาดหวัง:**
- ✅ สีเขียว = ตั้งค่าถูกต้อง
- ❌ สีแดง = ต้องแก้ไข (จำเป็น)
- ⚠️ สีเหลือง = แนะนำให้ตั้งค่า (ตัวเลือก)

### 2. ทดสอบการเชื่อมต่อฐานข้อมูล

```bash
# ทดสอบการเชื่อมต่อฐานข้อมูล
cd apps/worker
python -c "
import asyncio
from app.database.connection import test_connection
asyncio.run(test_connection())
"
```

### 3. ทดสอบการเชื่อมต่อ Redis

```bash
# ทดสอบการเชื่อมต่อ Redis
cd apps/worker
python -c "
from app.database.redis import test_redis_connection
test_redis_connection()
"
```

### 4. ทดสอบ LLM Providers

```bash
# ทดสอบ OpenRouter connection
cd apps/worker
python -c "
from app.services.llm_client import test_provider
test_provider('openrouter')
"
```

---

## 🚀 การเริ่มต้นใช้งาน

### 1. รัน Migration

```bash
# สร้างตารางฐานข้อมูล
cd apps/worker
python -m alembic upgrade head
```

### 2. เริ่มต้น FastAPI Worker

```bash
# ใน terminal 1 - FastAPI Worker
cd apps/worker
python main.py

# หรือใช้ uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. เริ่มต้น Cloudflare Worker (หากต้องการ)

```bash
# ใน terminal 2 - Cloudflare Worker
cd apps/bridge
npm install
npm run dev
```

### 4. ทดสอบ API

```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs
```

---

## 🐛 การแก้ไขปัญหา

### ปัญหาที่พบบ่อย

#### 1. Database Connection Error
```bash
# ตรวจสอบ connection string
echo $DB_DSN

# ทดสอบการเชื่อมต่อด้วย psql (หากติดตั้ง)
psql $DB_DSN
```

#### 2. Redis Connection Error
```bash
# ตรวจสอบ Upstash URL
echo $UPSTASH_REDISURL

# ทดสอบการเชื่อมต่อ
redis-cli -u $UPSTASH_REDISURL ping
```

#### 3. LLM Provider Error
```bash
# ตรวจสอบ API key format
echo $OPENROUTER_TOKEN | head -c 10

# ทดสอบ API key
curl -H "Authorization: Bearer $OPENROUTER_TOKEN" \
     https://openrouter.ai/api/v1/models
```

#### 4. Environment Variable Not Found
```bash
# ตรวจสอบไฟล์ .env
cat .env | grep -E "OPENROUTER_TOKEN|JWT_SECRET|ENCRYPTION_KEY"

# ตรวจสอบว่าไฟล์ .env ถูก load หรือไม่ (export เข้า environment)
set -a
source .env
set +a
echo $OPENROUTER_TOKEN
```

### Logs และ Debugging

```bash
# ดู logs ของ FastAPI
cd apps/worker
tail -f logs/app.log

# ดู error logs
tail -f logs/error.log

# ตั้งค่า debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG
```

### แหล่งข้อมูลเพิ่มเติม

- 📚 [API Documentation](http://localhost:8000/docs)
- 🔍 [ROADMAP.md](ROADMAP.md) - แผนการพัฒนา
- 🏗️ [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - ภาพรวมโปรเจ็ค
- 🐛 [GitHub Issues](https://github.com/your-repo/issues)

---

## 📞 การขอความช่วยเหลือ

หากพบปัญหาหรือต้องการความช่วยเหลือ:

1. **ตรวจสอบ Logs** ใน `/logs/` directory
2. **รัน Validation Script** `./scripts/validate_secrets.sh` (อ่านค่าจาก `.env` อัตโนมัติ)
3. **อ่าน Documentation** ใน `docs/` directory
4. **เปิด Issue** ใน GitHub repository

---

## ✅ Checklist ก่อนเริ่มใช้งาน

- [ ] Clone repository สำเร็จ
- [ ] ติดตั้ง dependencies ครบถ้วน
- [ ] สร้าง accounts กับ providers ที่จำเป็น
- [ ] ได้ API keys ครบถ้วน
- [ ] ตั้งค่า .env files ถูกต้อง
- [ ] รัน validation script ผ่าน
- [ ] ทดสอบการเชื่อมต่อฐานข้อมูล
- [ ] ทดสอบการเชื่อมต่อ Redis
- [ ] ทดสอบ LLM providers
- [ ] รัน migration scripts สำเร็จ
- [ ] เริ่มต้น FastAPI worker สำเร็จ

🎉 **เมื่อผ่าน checklist ทั้งหมดแล้ว คุณพร้อมใช้งาน bl1nk-agent-builder แล้ว!**
