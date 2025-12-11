---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: "00000000000000000000000000000000"
    PropagateID: "00000000000000000000000000000000"
    ReservedCode1: 3046022100927c9e961a5c70539a7c00ad2e610e52520c0b7a48438cd8be00e7107d672fef022100b9f0bf9068ec0183051171950c3378e5984d500ae138ab3fa3baf6cb4671da82
    ReservedCode2: 304502207981aa7319853706e2be862a1b3f56a42059df894f1878f8285ab1c8828765b5022100a38bca02b4debb611aab94debaa9a5c3b7fe3ad84c82644cdf5fce27d418082e
---

# 🤖 AGENTS.md - คู่มือสำหรับ AI Agents

## คู่มือการทำงานของ AI Agents กับโปรเจ็ค bl1nk-agent-builder

### 📋 สารบัญ

1. [บทบาทและความรับผิดชอบ](#บทบาทและความรับผิดชอบ)
2. [การทำงานร่วมกันของ Agents](#การทำงานร่วมกันของ-agents)
3. [การพัฒนาและปรับปรุง](#การพัฒนาและปรับปรุง)
4. [Testing และ Quality Assurance](#testing-และ-quality-assurance)
5. [การ Deploy และ Monitoring](#การ-deploy-และ-monitoring)
6. [Documentation และ Knowledge Transfer](#documentation-และ-knowledge-transfer)

---

## 🎯 บทบาทและความรับผิดชอบ

### 🔧 **Backend Agent** - FastAPI Worker Development

**หน้าที่หลัก:**
- พัฒนาและปรับปรุง FastAPI backend applications
- จัดการ API endpoints และ business logic
- พัฒนา database models และ migrations
- สร้างและปรับปรุง middleware stack
- จัดการ error handling และ logging

**ไฟล์และโมดูลที่ต้องดูแล:**
```
apps/worker/app/
├── main.py                 # FastAPI application entry point
├── config/                # Configuration management
├── database/              # Database connections และ models
├── middleware/            # CORS, Auth, Tracing middleware
├── routes/                # API endpoints
├── services/              # Business logic services
├── models/                # Pydantic models และ schemas
└── utils/                 # Utility functions
```

**ความเชี่ยวชาญที่ต้องมี:**
- Python 3.11+ และ FastAPI framework
- PostgreSQL และ SQLAlchemy ORM
- Redis และ async programming
- AsyncIO และ concurrent programming
- API design และ OpenAPI specifications

---

### 🌐 **Frontend Agent** - Cloudflare Worker Development

**หน้าที่หลัก:**
- พัฒนาและปรับปรุง Cloudflare Workers
- จัดการ edge computing และ request routing
- พัฒนา signature verification และ security middleware
- จัดการ payload transformation และ API mapping
- ปรับปรุง performance และ caching strategies

**ไฟล์และโมดูลที่ต้องดูแล:**
```
apps/bridge/
├── src/
│   ├── index.ts           # Worker entry point
│   ├── map_payload.ts     # Payload transformation
│   └── signature.ts       # Webhook signature verification
└── wrangler.toml          # Worker configuration
```

**ความเชี่ยวชาญที่ต้องมี:**
- TypeScript และ Cloudflare Workers
- Edge computing concepts
- Web APIs และ HTTP protocols
- Security และ cryptography
- Performance optimization

---

### 🗄️ **Database Agent** - PostgreSQL & Vector Database

**หน้าที่หลัก:**
- ออกแบบและปรับปรุง database schema
- จัดการ PostgreSQL และ pgvector extensions
- สร้างและปรับปรุง migration scripts
- จัดการ indexing strategies สำหรับ vector search
- ปรับปรุง query performance และ optimization

**ไฟล์และโมดูลที่ต้องดูแล:**
```
sql/migrations/             # Database migrations
apps/worker/app/database/   # Database connection และ models
```

**ความเชี่ยวชาญที่ต้องมี:**
- PostgreSQL administration
- SQL และ database design
- Vector databases (pgvector)
- Indexing และ performance tuning
- Data modeling และ normalization

---

### 🚀 **DevOps Agent** - Infrastructure & Deployment

**หน้าที่หลัก:**
- จัดการ CI/CD pipelines
- ตั้งค่าและจัดการ Docker containers
- ออกแบบและปรับปรุง infrastructure
- จัดการ environment configurations
- ตั้งค่า monitoring และ logging systems

**ไฟล์และโมดูลที่ต้องดูแล:**
```
infra/                     # Infrastructure code
scripts/                   # Deployment และ setup scripts
.github/workflows/         # CI/CD pipelines
Dockerfile                 # Container definitions
```

**ความเชี่ยวชาญที่ต้องมี:**
- Docker และ containerization
- CI/CD tools (GitHub Actions)
- Cloud platforms (AWS, Cloudflare)
- Infrastructure as Code
- Monitoring และ logging

---

### 🔒 **Security Agent** - Authentication & Authorization

**หน้าที่หลัก:**
- พัฒนาและปรับปรุง authentication systems
- จัดการ JWT token handling
- สร้างและปรับปรุง authorization middleware
- จัดการ API security และ rate limiting
- ปรับปรุง encryption และ data protection

**ไฟล์และโมดูลที่ต้องดูแล:**
```
apps/worker/app/middleware/auth.py
apps/worker/app/services/oauth.py
config/env.example         # Security configurations
```

**ความเชี่ยวชาญที่ต้องมี:**
- JWT และ OAuth2 protocols
- API security best practices
- Encryption และ cryptography
- Authentication systems
- Security auditing

---

### 🤖 **ML/AI Agent** - LLM Integration & Vector Search

**หน้าที่หลัก:**
- จัดการ LLM provider integrations
- พัฒนา embedding และ vector search systems
- สร้างและปรับปรุง RAG (Retrieval-Augmented Generation)
- จัดการ multi-agent coordination
- ปรับปรุง AI model selection และ routing

**ไฟล์และโมดูลที่ต้องดูแล:**
```
apps/worker/app/services/
├── llm_client.py          # LLM provider management
├── vector_store.py        # Vector search implementation
├── embed_client.py        # Embedding services
└── task_orchestrator.py   # Multi-agent coordination
```

**ความเชี่ยวชาญที่ต้องมี:**
- Large Language Models (LLMs)
- Vector databases และ embeddings
- RAG systems และ retrieval strategies
- AI model selection และ routing
- Machine learning pipelines

---

## 🤝 การทำงานร่วมกันของ Agents

### การประสานงานระหว่าง Agents

**1. การพัฒนา Feature ใหม่:**
```
Frontend Agent → Backend Agent → Database Agent → DevOps Agent → Security Agent → ML/AI Agent
```

**2. การ Deploy และ Monitoring:**
```
DevOps Agent → Backend Agent → Frontend Agent → Security Agent
```

**3. การแก้ไขปัญหา:**
```
Any Agent → Security Agent (Security issues) → Database Agent (DB issues) → ML/AI Agent (AI issues)
```

### การสื่อสารและ Coordination

**Slack Channels ที่แนะนำ:**
- `#bl1nk-development` - Development discussions
- `#bl1nk-deployments` - Deployment coordination
- `#bl1nk-issues` - Issue tracking และ resolution
- `#bl1nk-security` - Security-related discussions

**Meeting Schedule:**
- **Daily Standup** - 09:00 (ทุก agent report progress)
- **Weekly Planning** - วันจันทร์ 10:00 (plan next week)
- **Sprint Review** - วันศุกร์ 16:00 (demo completed work)

---

## 🛠️ การพัฒนาและปรับปรุง

### Code Standards และ Conventions

**Python (Backend):**
```python
# ใช้ type hints
from typing import List, Optional, Dict, Any

async def process_task(
    task_id: str,
    parameters: Dict[str, Any],
    user_id: str
) -> Optional[TaskResult]:
    """Process a task with given parameters."""
    pass

# ใช้ Pydantic models
from pydantic import BaseModel, Field

class TaskRequest(BaseModel):
    task_id: str = Field(..., description="Unique task identifier")
    parameters: Dict[str, Any] = Field(..., description="Task parameters")
    user_id: str = Field(..., description="User who initiated the task")
```

**TypeScript (Frontend):**
```typescript
// ใช้ strict type checking
interface TaskRequest {
  task_id: string;
  parameters: Record<string, unknown>;
  user_id: string;
}

export async function processTask(
  request: TaskRequest
): Promise<TaskResponse> {
  // Implementation
}
```

### Git Workflow

**Branch Naming Convention:**
```
feature/agent-name/feature-description
fix/agent-name/issue-description
hotfix/agent-name/critical-fix
refactor/agent-name/refactoring-description
```

**Commit Message Format:**
```
agent-name: brief description of changes

- Detailed change 1
- Detailed change 2
- Detailed change 3

Issue: #123
```

**Pull Request Process:**
1. Create feature branch from `develop`
2. Implement changes และ add tests
3. Update documentation if needed
4. Create PR with detailed description
5. Request review from relevant agents
6. Address review comments
7. Merge after approval

---

## 🧪 Testing และ Quality Assurance

### Testing Strategy

**Unit Tests:**
```python
# apps/worker/tests/test_services/test_task_orchestrator.py
import pytest
from app.services.task_orchestrator import TaskOrchestrator

@pytest.mark.asyncio
async def test_task_orchestration():
    orchestrator = TaskOrchestrator()
    result = await orchestrator.process_task("test_task", {})
    assert result.status == "completed"
```

**Integration Tests:**
```python
# apps/worker/tests/integration/test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.mark.asyncio
async def test_create_task_endpoint():
    client = TestClient(app)
    response = client.post("/api/v1/tasks", json={
        "type": "text_generation",
        "parameters": {"prompt": "Hello world"}
    })
    assert response.status_code == 201
```

**E2E Tests:**
```typescript
// apps/bridge/tests/e2e/workflow.test.ts
import { Worker } from '@cloudflare/workers-types';

describe('End-to-End Workflow', () => {
  it('should process complete request flow', async () => {
    // Test complete workflow from edge to core
  });
});
```

### Quality Gates

**ก่อน Merge:**
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Code coverage > 80%
- [ ] No security vulnerabilities
- [ ] Performance benchmarks pass
- [ ] Documentation updated

**Performance Benchmarks:**
```bash
# รัน performance tests
./scripts/run_benchmarks.sh

# ตรวจสอบ memory usage
python -m memory_profiler apps/worker/main.py

# Load testing
artillery run tests/load/test_api_load.yml
```

---

## 🚀 การ Deploy และ Monitoring

### Deployment Pipeline

**Development Environment:**
```bash
# Auto-deploy จาก feature branches
git push origin feature/backend/new-endpoint
# → GitHub Actions จะ deploy ไปที่ dev environment
```

**Staging Environment:**
```bash
# Deploy จาก develop branch
git checkout develop
git merge feature/backend/new-endpoint
git push origin develop
# → GitHub Actions จะ deploy ไปที่ staging environment
```

**Production Environment:**
```bash
# Deploy จาก main branch
git checkout main
git merge develop
git tag v1.2.3
git push origin main --tags
# → GitHub Actions จะ deploy ไปที่ production environment
```

### Monitoring และ Alerting

**Application Metrics:**
```python
# เพิ่ม custom metrics
from prometheus_client import Counter, Histogram, Gauge

# Request counter
REQUEST_COUNT = Counter(
    'bl1nk_requests_total',
    'Total requests processed',
    ['method', 'endpoint', 'status']
)

# Response time histogram
REQUEST_DURATION = Histogram(
    'bl1nk_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)
```

**Health Checks:**
```python
# apps/worker/app/routes/health.py
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "database": await check_database_connection(),
        "redis": await check_redis_connection(),
        "llm_providers": await check_llm_providers()
    }
```

**Alert Rules:**
```yaml
# monitoring/alerts.yml
groups:
  - name: bl1nk_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(bl1nk_requests_total{status="5xx"}[5m]) > 0.05
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
```

---

## 📚 Documentation และ Knowledge Transfer

### Documentation Standards

**API Documentation:**
```python
# apps/worker/app/routes/tasks.py
@app.post("/api/v1/tasks", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user)
) -> TaskResponse:
    """
    Create a new task for processing.
    
    Args:
        task: Task creation data including type and parameters
        current_user: Authenticated user creating the task
        
    Returns:
        TaskResponse: Created task with status and ID
        
    Raises:
        HTTPException: If task creation fails
        ValidationError: If task parameters are invalid
    """
```

**Architecture Documentation:**
```markdown
# docs/architecture/database-design.md
## Database Schema Overview

### Users Table
- Primary key: `id` (UUID)
- Authentication: `email`, `password_hash`
- Profile: `name`, `avatar_url`
- Billing: `subscription_tier`, `usage_limits`

### Tasks Table
- Primary key: `id` (UUID)
- Relationships: `user_id` → Users
- Status tracking: `status`, `progress`, `result`
- Metadata: `created_at`, `updated_at`, `metadata`
```

### Knowledge Sharing

**Weekly Knowledge Sharing Sessions:**
- **Monday 15:00** - Technical deep dives
- **Wednesday 15:00** - Architecture discussions
- **Friday 15:00** - Retrospectives และ lessons learned

**Documentation Updates:**
- Update README.md เมื่อมี feature ใหม่
- Update API documentation เมื่อมี endpoint ใหม่
- Update architecture diagrams เมื่อมีการเปลี่ยนแปลง
- Update deployment guides เมื่อมีการปรับปรุง infrastructure

---

## 🎯 เป้าหมายและ KPIs

### Technical KPIs

**Performance:**
- API response time < 200ms (p95)
- Database query time < 100ms (p95)
- Task processing time < 30s (p95)
- System uptime > 99.9%

**Quality:**
- Code coverage > 80%
- Bug resolution time < 24h (critical), < 72h (major)
- Security vulnerabilities = 0
- Documentation completeness > 95%

**Scalability:**
- Support 10,000+ concurrent users
- Handle 1M+ requests per day
- Auto-scale based on load
- Zero-downtime deployments

### Development KPIs

**Velocity:**
- Sprint velocity tracking
- Feature delivery time
- Bug fix time
- Code review turnaround time

**Quality:**
- Pull request review time
- Test coverage percentage
- Code complexity metrics
- Technical debt ratio

---

## 📞 Contact Information

**Primary Contacts:**
- **Project Lead**: [Name] - [email] - [slack]
- **Technical Lead**: [Name] - [email] - [slack]
- **DevOps Lead**: [Name] - [email] - [slack]

**Emergency Contacts:**
- **Security Issues**: [security-email] - [security-phone]
- **Production Issues**: [ops-email] - [ops-phone]

**Communication Channels:**
- **GitHub Issues**: [repository-url]/issues
- **Slack Workspace**: [workspace-url]
- **Documentation**: [docs-url]
- **Monitoring Dashboard**: [monitoring-url]

---

## 📋 Agent Onboarding Checklist

**สำหรับ Agent ใหม่:**

- [ ] อ่าน PROJECT_SUMMARY.md
- [ ] อ่าน ROADMAP.md
- [ ] อ่าน QUICK_START_GUIDE.md
- [ ] ตั้งค่า development environment
- [ ] รัน validation scripts
- [ ] ทดสอบการเชื่อมต่อ services
- [ ] อ่าน codebase documentation
- [ ] เข้าร่วม team meetings
- [ ] ตั้งค่า monitoring และ alerting
- [ ] ทดสอบ deployment process
- [ ] สร้าง first contribution
- [ ] เข้าร่วม knowledge sharing sessions

**Welcome to the bl1nk-agent-builder team! 🎉**