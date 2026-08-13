# bl1nk-agent-builder Technology Stack

## Backend (Python)

### Core Framework
- **FastAPI 0.104+** - Modern async web framework
- **Python 3.11+** - Runtime environment
- **Uvicorn 0.24+** - ASGI server

### Database & Caching
- **asyncpg 0.29+** - Async PostgreSQL driver
- **psycopg 3.2+** - PostgreSQL adapter
- **pgvector 0.2+** - Vector similarity search for PostgreSQL
- **redis 5.0+** - Redis client for caching/sessions
- **SQLAlchemy** (via asyncpg) - ORM patterns

### LLM & AI
- **litellm 1.13+** - Multi-provider LLM abstraction
- **openai 1.3+** - OpenAI API client
- **tiktoken 0.12+** - Token counting for OpenAI models
- **huggingface-hub 1.2+** - Hugging Face model access

### Authentication & Security
- **python-jose 3.3+** - JWT token handling
- **passlib 1.7+** - Password hashing (bcrypt)
- **cryptography 41.0+** - Encryption utilities
- **python-multipart 0.0.6** - Form data parsing

### Observability & Monitoring
- **opentelemetry-api 1.21+** - Tracing API
- **opentelemetry-sdk 1.21+** - Tracing implementation
- **opentelemetry-instrumentation-fastapi 0.42b0** - FastAPI instrumentation
- **opentelemetry-instrumentation-asgi 0.42b0** - ASGI instrumentation
- **structlog 23.2+** - Structured logging

### Utilities
- **pydantic 2.5+** - Data validation and settings
- **pydantic-settings 2.1+** - Environment configuration
- **python-dotenv 1.0+** - .env file loading
- **arrow 1.3+** - Date/time utilities
- **tenacity 8.2+** - Retry logic
- **slowapi 0.1.9** - Rate limiting
- **sse-starlette 1.8+** - Server-Sent Events
- **aiofiles 23.2+** - Async file operations
- **aiohttp 3.9+** - Async HTTP client
- **httpx 0.25+** - HTTP client library
- **requests 2.31+** - HTTP library
- **orjson 3.9+** - Fast JSON serialization
- **rich 13.7+** - Terminal formatting
- **typer 0.9+** - CLI framework

### Development Tools
- **pytest 7.4+** - Testing framework
- **pytest-asyncio 0.21+** - Async test support
- **pytest-cov 4.1+** - Coverage reporting
- **black 23.11+** - Code formatter
- **isort 5.12+** - Import sorting
- **mypy 1.7+** - Static type checking
- **ruff 0.1+** - Fast Python linter
- **pre-commit 3.6+** - Git hooks framework

## Frontend (TypeScript/JavaScript)

### Edge Computing
- **Cloudflare Workers** - Serverless edge computing
- **wrangler 3.101+** - Cloudflare Workers CLI
- **@cloudflare/workers-types 4.20+** - Type definitions

### Core Dependencies
- **TypeScript 5.7+** - Type-safe JavaScript
- **Node.js 20.x** - Runtime environment
- **esbuild 0.24+** - JavaScript bundler
- **uuid 10.0+** - UUID generation
- **jose 5.9+** - JWT handling
- **ajv 8.17+** - JSON schema validation
- **ajv-formats 3.0+** - Format validators

### Development Tools
- **eslint 9.15+** - JavaScript linter
- **prettier 3.4+** - Code formatter
- **eslint-config-prettier 9.1+** - ESLint + Prettier integration
- **eslint-plugin-prettier 5.2+** - Prettier as ESLint rule

### Optional UI (Next.js)
- **Next.js** - React framework
- **React** - UI library
- **@vercel/analytics 1.6+** - Analytics integration
- **ai 5.0+** - AI SDK for streaming

## Infrastructure & DevOps

### Containerization
- **Docker** - Container runtime
- **Docker Compose** - Multi-container orchestration
- **Dockerfile.worker** - Python backend image

### Databases (Serverless)
- **PostgreSQL 15+** (Neon) - Relational database
- **Redis** (Upstash) - In-memory cache/queue
- **pgvector** - Vector similarity search extension

### Monitoring & Observability
- **Prometheus** - Metrics collection
- **Grafana** - Metrics visualization
- **OpenTelemetry** - Distributed tracing

### CI/CD
- **GitHub Actions** - Workflow automation
- **CI Pipeline** (.github/workflows/ci.yml)
- **CD Pipeline** (.github/workflows/cd.yml)

## Configuration Management

### Environment Variables
- `.env` - Local development
- `.env.docker` - Docker environment
- `config/env.example` - Template

### Configuration Files
- `config/settings.py` - Pydantic settings
- `config/provider_routing.yaml` - LLM routing rules
- `config/providermodels.yaml` - Available models
- `config/billing_thresholds.yaml` - Cost thresholds
- `config/monthly_budget.yaml` - Budget limits

## Development Commands

### Setup & Installation
```bash
# Bootstrap project
./scripts/bootstrap.sh development

# Install Python dependencies
pip install -r apps/worker/requirements.txt

# Install Node dependencies
cd apps/bridge && npm install
cd apps/worker && npm install (if applicable)
```

### Local Development
```bash
# Start all services
make dev

# Or manually:
# Terminal 1: FastAPI backend
cd apps/worker && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Cloudflare Workers
cd apps/bridge && wrangler dev

# Terminal 3: Next.js UI (optional)
cd ui/nextjs && npm run dev
```

### Code Quality
```bash
# Format code
make format

# Lint code
make lint

# Type checking
make type-check

# Security audit
make security-audit
```

### Testing
```bash
# Run all tests
make test

# Test with coverage
make test-coverage

# Load testing
make load-test

# Integration tests
make integration-test
```

### Database
```bash
# Run migrations
./scripts/run_migrations.sh

# Generate sample data
./scripts/generate_sample_data.sh
```

### Deployment
```bash
# Production deployment
./scripts/deploy.sh production

# Staging deployment
./scripts/deploy.sh staging

# Health check
./scripts/health_check.sh

# Billing monitoring
./scripts/billing_monitor.sh
```

### Utilities
```bash
# Generate API keys
./scripts/generate_api_keys.sh

# Validate secrets
./scripts/validate_secrets.sh

# Project status
./scripts/project_status.sh

# Verify structure
./scripts/verify_structure.sh
```

## API Endpoints

### Health & Status
- `GET /health` - Service health check
- `GET /health/providers` - Provider status
- `GET /metrics` - Prometheus metrics

### Core API
- `POST /api/v1/chat` - Chat completion
- `POST /api/v1/rag/query` - RAG query
- `POST /api/v1/tasks` - Create task
- `GET /api/v1/tasks/{id}` - Get task status

### Admin
- `GET /admin/costs` - Cost tracking
- `GET /admin/usage` - Usage statistics
- `POST /admin/alerts` - Configure alerts

### Webhooks
- `POST /webhooks/github` - GitHub events
- `POST /webhooks/slack` - Slack events
- `POST /webhooks/poe` - Poe events
- `POST /webhooks/manus` - Manus events

### MCP
- `POST /mcp/tools` - Tool execution
- `GET /mcp/tools` - List available tools

## Performance Characteristics

### Response Times
- Edge (Cloudflare): <100ms
- API (FastAPI): <500ms
- RAG Query: <1s (with caching)
- LLM Response: 2-30s (depends on model)

### Scalability
- Horizontal scaling via Cloudflare Workers
- Database connection pooling (asyncpg)
- Redis caching for frequently accessed data
- Rate limiting per user/provider

### Resource Limits
- Max request size: 10MB
- Max response timeout: 30s
- Rate limits: Configurable per endpoint
- Concurrent connections: Limited by database pool

## Supported LLM Providers

1. **OpenRouter** - 100+ models, cost-effective
2. **Cloudflare AI** - Edge-native models
3. **AWS Bedrock** - Enterprise models
4. **Anthropic** - Claude models
5. **OpenAI** - GPT models (via OpenRouter)

## Version Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.11+ | Required for FastAPI async |
| Node.js | 20.x | For Cloudflare Workers |
| PostgreSQL | 15+ | pgvector support |
| Redis | 7.0+ | Serverless via Upstash |
| Docker | 20.10+ | For containerization |
| TypeScript | 5.0+ | For type safety |
