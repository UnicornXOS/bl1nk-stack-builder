#!/usr/bin/env python3
"""
bl1nk-agent-builder FastAPI Worker
Main application entry point for the core API service
"""

import logging
import sys
import signal
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import configuration
from app.config.settings import settings
from app.database.connection import init_db, close_db
from app.database.redis import init_redis, close_redis

# Import route modules
from app.routes import webhook_poe, webhook_manus, webhook_slack, webhook_github
from app.routes import tasks, skills, mcp, health, admin
from app.routes.metrics import metrics_router

# Import middleware
from app.middleware.cors import setup_cors
from app.middleware.auth import setup_auth
from app.middleware.tracing import setup_tracing

# Import services
from app.services.task_orchestrator import TaskOrchestrator
from app.services.provider_manager import ProviderManager
from app.services.vector_store import VectorStore

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/app.log") if settings.log_file else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Global service instances
task_orchestrator: TaskOrchestrator = None
provider_manager: ProviderManager = None
vector_store: VectorStore = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan management
    Handles startup and shutdown procedures
    """
    logger.info("Starting bl1nk-agent-builder FastAPI Worker...")
    
    try:
        # Initialize database
        logger.info("Initializing database connection...")
        await init_db()
        
        # Initialize Redis
        logger.info("Initializing Redis connection...")
        await init_redis()
        
        # Initialize services
        global task_orchestrator, provider_manager, vector_store
        
        logger.info("Initializing services...")
        provider_manager = ProviderManager()
        vector_store = VectorStore()
        task_orchestrator = TaskOrchestrator(provider_manager, vector_store)
        
        # Store services in app state
        app.state.task_orchestrator = task_orchestrator
        app.state.provider_manager = provider_manager
        app.state.vector_store = vector_store
        
        logger.info("Services initialized successfully")
        logger.info("Application startup completed")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    finally:
        logger.info("Shutting down application...")
        
        # Cleanup services
        if task_orchestrator:
            await task_orchestrator.cleanup()
        
        # Close Redis connection
        await close_redis()
        
        # Close database connection
        await close_db()
        
        logger.info("Application shutdown completed")


# Create FastAPI application
app = FastAPI(
    title="bl1nk-agent-builder API",
    description="""
    AI Agent Platform with RAG, multi-agent, MCP integration, and compliance.
    
    ## Architecture
    - **Edge**: Cloudflare Workers (proxy)
    - **Core**: FastAPI (this service)
    - **Database**: Neon Postgres + pgvector
    - **Queue**: Upstash Redis
    - **Storage**: Cloudflare R2
    
    ## Features
    - Webhook receivers for Poe, Manus, Slack, GitHub
    - Task management with SSE streaming
    - Skill invocation and MCP tool integration
    - Vector search and embeddings
    - Multi-provider LLM routing
    - Rate limiting and cost controls
    """,
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    lifespan=lifespan,
    debug=settings.debug
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# =============================================================================
# MIDDLEWARE SETUP
# =============================================================================

# Trusted hosts middleware
if settings.trusted_hosts:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.trusted_hosts
    )

# CORS middleware
setup_cors(app)

# Tracing middleware
setup_tracing(app)

# Authentication middleware
setup_auth(app)


# =============================================================================
# API ROUTES
# =============================================================================

# Health and monitoring
app.include_router(
    health.router,
    prefix="/health",
    tags=["Health"]
)

app.include_router(
    metrics_router,
    prefix="/metrics",
    tags=["Metrics"]
)

# Admin routes (protected)
app.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin"]
)

# Webhook routes
app.include_router(
    webhook_poe.router,
    prefix="/webhook",
    tags=["Webhooks"]
)

app.include_router(
    webhook_manus.router,
    prefix="/webhook",
    tags=["Webhooks"]
)

app.include_router(
    webhook_slack.router,
    prefix="/webhook",
    tags=["Webhooks"]
)

app.include_router(
    webhook_github.router,
    prefix="/webhook",
    tags=["Webhooks"]
)

# Core API routes
app.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["Tasks"]
)

app.include_router(
    skills.router,
    prefix="/skills",
    tags=["Skills"]
)

app.include_router(
    mcp.router,
    prefix="/mcp",
    tags=["MCP"]
)


# =============================================================================
# GLOBAL ERROR HANDLERS
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with proper error format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.detail,
            "trace_id": getattr(request.state, "trace_id", "unknown"),
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all uncaught exceptions"""
    logger.error(
        f"Uncaught exception: {exc}",
        extra={
            "trace_id": getattr(request.state, "trace_id", "unknown"),
            "url": str(request.url),
            "method": request.method
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "trace_id": getattr(request.state, "trace_id", "unknown")
        }
    )


# =============================================================================
# STARTUP AND SHUTDOWN HANDLERS
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Application startup event triggered")
    
    # Create necessary directories
    import os
    os.makedirs("logs", exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    
    logger.info("Startup event completed")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Application shutdown event triggered")
    
    # Cleanup is handled by lifespan context manager
    logger.info("Shutdown event completed")


# =============================================================================
# SIGNAL HANDLERS
# =============================================================================

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)


# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Configure uvicorn
    config = {
        "app": app,
        "host": settings.host,
        "port": settings.port,
        "reload": settings.reload,
        "workers": settings.workers if not settings.reload else 1,
        "log_config": None,  # Use our custom logging
        "access_log": True,
        "error_log": True
    }
    
    # Add SSL configuration if enabled
    if settings.ssl_cert and settings.ssl_key:
        config.update({
            "ssl_certfile": settings.ssl_cert,
            "ssl_keyfile": settings.ssl_key,
            "ssl_ca_certs": settings.ssl_ca_certs,
            "ssl_cert_reqs": settings.ssl_cert_reqs
        })
    
    logger.info(f"Starting server on {settings.host}:{settings.port}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Run server
    uvicorn.run(**config)