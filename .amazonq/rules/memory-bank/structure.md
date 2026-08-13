# bl1nk-agent-builder Project Structure

## Directory Organization

```
bl1nk-agent-builder/
├── apps/                          # Application services
│   ├── bridge/                    # Cloudflare Workers edge proxy
│   │   ├── src/                   # TypeScript source
│   │   ├── wrangler.toml          # Cloudflare Workers config
│   │   └── package.json           # Node.js dependencies
│   └── worker/                    # FastAPI Python backend
│       ├── app/                   # Main application code
│       │   ├── config/            # Configuration management
│       │   ├── database/          # Database connections (PostgreSQL, Redis)
│       │   ├── middleware/        # Auth, CORS, tracing middleware
│       │   ├── models/            # Pydantic schemas and AI models
│       │   ├── routes/            # API endpoints and webhooks
│       │   ├── services/          # Business logic (LLM, RAG, orchestration)
│       │   ├── utils/             # Utilities (retry, SSE, tracing)
│       │   └── main.py            # FastAPI application entry point
│       ├── requirements.txt       # Python dependencies
│       └── .env                   # Environment variables
├── config/                        # Configuration files
│   ├── provider_routing.yaml      # LLM provider routing rules
│   ├── providermodels.yaml        # Available models per provider
│   ├── billing_thresholds.yaml    # Cost thresholds
│   ├── monthly_budget.yaml        # Budget limits
│   └── env.example                # Environment template
├── data/                          # Data directories
│   ├── postgres/                  # PostgreSQL data volume
│   └── redis/                     # Redis data volume
├── docs/                          # Documentation
│   ├── ADMIN_DASHBOARD.md         # Admin features
│   └── WINDOW_INSTALLATION.md     # Windows setup guide
├── infra/                         # Infrastructure configs
│   ├── grafana/                   # Grafana dashboards
│   └── prometheus/                # Prometheus metrics config
├── packages/                      # Shared packages
│   └── schema/                    # OpenAPI schema definitions
├── scripts/                       # Automation scripts
│   ├── bootstrap.sh               # Initial setup
│   ├── dev.sh                     # Development startup
│   ├── deploy.sh                  # Deployment automation
│   ├── health_check.sh            # Service health verification
│   ├── billing_monitor.sh         # Cost monitoring
│   └── [other utility scripts]
├── sql/                           # Database migrations
│   └── migrations/
│       ├── 001_create_tables.sql  # Initial schema
│       └── 002_add_indexes.sql    # Performance indexes
├── ui/                            # Frontend (optional)
│   └── nextjs/                    # Next.js application
├── .github/                       # GitHub workflows
│   └── workflows/
│       ├── ci.yml                 # Continuous integration
│       └── cd.yml                 # Continuous deployment
├── .amazonq/                      # Amazon Q configuration
│   └── rules/                     # Custom rules and memory bank
├── docker-compose.yml             # Local development orchestration
├── Dockerfile.worker              # Python backend container
├── Makefile                       # Development commands
├── package.json                   # Root Node.js config
├── README.md                      # Project documentation
└── [configuration files]          # .env, .gitignore, etc.
```

## Core Components

### 1. Edge Layer (Cloudflare Workers)
**Location**: `apps/bridge/`

Handles:
- Request routing and proxying
- Authentication and rate limiting
- Request/response transformation
- Edge-level caching

**Key Files**:
- `src/index.ts` - Main worker handler
- `wrangler.toml` - Cloudflare configuration

### 2. Core Backend (FastAPI)
**Location**: `apps/worker/app/`

#### Config Module (`config/`)
- `settings.py` - Centralized configuration management
- Environment variable loading and validation

#### Database Module (`database/`)
- `connection.py` - PostgreSQL connection pool (asyncpg)
- `redis.py` - Redis client for caching and sessions
- Connection lifecycle management

#### Middleware Module (`middleware/`)
- `auth.py` - JWT authentication and authorization
- `cors.py` - CORS policy configuration
- `tracing.py` - OpenTelemetry instrumentation
- Request/response logging

#### Models Module (`models/`)
- `schemas.py` - Pydantic request/response schemas
- `bedrock_agentcore.py` - AWS Bedrock agent integration
- Data validation and serialization

#### Routes Module (`routes/`)
- `health.py` - Health check endpoints
- `tasks.py` - Task management API
- `skills.py` - Agent skills registry
- `mcp.py` - Model Context Protocol endpoints
- `metrics.py` - Prometheus metrics endpoint
- `admin.py` - Administrative endpoints
- `webhook_*.py` - Webhook handlers (GitHub, Slack, Poe, Manus)

#### Services Module (`services/`)
- `llm_client.py` - Multi-provider LLM abstraction (OpenRouter, Bedrock, etc.)
- `task_orchestrator.py` - Task distribution and coordination
- `vector_store.py` - RAG vector search with pgvector
- `embed_client.py` - Embedding generation
- `billing.py` - Cost tracking and budget management
- `github_app.py` - GitHub integration
- `oauth.py` - OAuth authentication flows
- `processor.py` - Request processing pipeline

#### Utils Module (`utils/`)
- `retry.py` - Exponential backoff retry logic
- `sse.py` - Server-Sent Events streaming
- `tracing.py` - Distributed tracing utilities
- `alerting.py` - Alert and notification system
- `idempotency.py` - Idempotent request handling

#### Main Entry Point (`main.py`)
- FastAPI application initialization
- Route registration
- Middleware setup
- Startup/shutdown handlers

### 3. Data Layer
**PostgreSQL** (Neon serverless):
- User and authentication data
- Task history and logs
- Document storage with pgvector embeddings
- Audit logs

**Redis** (Upstash serverless):
- Session management
- Request caching
- Rate limit counters
- Task queues

### 4. Configuration Layer
**Location**: `config/`

- `provider_routing.yaml` - Rules for routing requests to LLM providers
- `providermodels.yaml` - Available models and their capabilities
- `billing_thresholds.yaml` - Cost thresholds and alerts
- `monthly_budget.yaml` - Budget limits per provider/user

### 5. Infrastructure & Monitoring
**Location**: `infra/`

- Prometheus configuration for metrics collection
- Grafana provisioning for dashboards
- OpenTelemetry instrumentation

### 6. Database Migrations
**Location**: `sql/migrations/`

- `001_create_tables.sql` - Initial schema with pgvector support
- `002_add_indexes.sql` - Performance optimization indexes

## Architectural Patterns

### Multi-Tier Architecture
```
Edge Layer (Cloudflare Workers)
    ↓
API Layer (FastAPI Routes)
    ↓
Service Layer (Business Logic)
    ↓
Data Layer (PostgreSQL + Redis)
```

### Provider Abstraction
LLM providers are abstracted through `llm_client.py`, allowing:
- Transparent provider switching
- Cost-aware routing
- Automatic fallback mechanisms
- Unified request/response handling

### Task Orchestration
`task_orchestrator.py` manages:
- Task distribution to agents
- Dependency resolution
- Parallel execution
- Result aggregation

### RAG Pipeline
`vector_store.py` implements:
- Document embedding and storage
- Semantic similarity search
- Context retrieval and injection
- Multi-document ranking

## Key Relationships

```
main.py (FastAPI App)
├── Routes (API endpoints)
│   └── Services (Business logic)
│       ├── llm_client (Provider routing)
│       ├── task_orchestrator (Agent coordination)
│       ├── vector_store (RAG)
│       └── billing (Cost tracking)
├── Middleware (Auth, CORS, Tracing)
├── Database (PostgreSQL, Redis)
└── Config (Settings management)
```

## Development Workflow

### Local Development
- `docker-compose.yml` orchestrates PostgreSQL, Redis, and FastAPI
- `Makefile` provides convenient commands
- `scripts/dev.sh` starts all services

### Testing
- Unit tests in `tests/` directory
- Integration tests for API endpoints
- Load testing for performance validation

### Deployment
- `scripts/deploy.sh` handles production deployment
- Docker images for containerization
- Cloudflare Workers deployment via `wrangler`

## Environment Separation

- **Local**: Docker Compose with local databases
- **Staging**: Neon PostgreSQL + Upstash Redis
- **Production**: Managed cloud services with monitoring
