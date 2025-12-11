"""
Health check endpoints for bl1nk-agent-builder
Provides health monitoring and status endpoints
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.database.connection import health_check as db_health_check
from app.database.redis import redis_health_check
from app.config.settings import settings

logger = logging.getLogger(__name__)

# Pydantic models for health responses
class HealthStatus(BaseModel):
    status: str
    timestamp: datetime
    service: str
    version: str
    environment: str


class DatabaseHealth(BaseModel):
    status: str
    connection: str
    pgvector: str
    tables: Dict[str, Any]


class RedisHealth(BaseModel):
    status: str
    ping: bool
    memory_used: str
    connected_clients: int
    queue_length: int


class SystemHealth(BaseModel):
    cpu_percent: float
    memory_percent: float
    uptime_seconds: float


class DetailedHealthResponse(BaseModel):
    overall_status: str
    api: HealthStatus
    database: DatabaseHealth
    redis: RedisHealth
    system: SystemHealth
    providers: Dict[str, str]


# Simple health endpoint
async def simple_health() -> Dict[str, str]:
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "service": "bl1nk-agent-builder",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "environment": settings.environment
    }


# Detailed health check
async def detailed_health() -> DetailedHealthResponse:
    """Detailed health check with all components"""
    
    # Check overall status
    overall_status = "healthy"
    
    # API health
    api_health = HealthStatus(
        status="healthy",
        timestamp=datetime.now(),
        service="bl1nk-agent-builder",
        version="1.0.0",
        environment=settings.environment
    )
    
    # Database health
    db_health = await db_health_check()
    if db_health["status"] != "healthy":
        overall_status = "degraded"
    
    database_health = DatabaseHealth(
        status=db_health["status"],
        connection=db_health["connection"],
        pgvector=db_health["pgvector"],
        tables=db_health["tables"]
    )
    
    # Redis health
    redis_health = await redis_health_check()
    if redis_health["status"] != "healthy":
        overall_status = "degraded"
    
    redis_detailed = RedisHealth(
        status=redis_health["status"],
        ping=redis_health.get("ping", False),
        memory_used=redis_health.get("memory_used", "unknown"),
        connected_clients=redis_health.get("connected_clients", 0),
        queue_length=redis_health.get("queue_length", 0)
    )
    
    # System health
    try:
        import psutil
        
        system_health = SystemHealth(
            cpu_percent=psutil.cpu_percent(interval=1),
            memory_percent=psutil.virtual_memory().percent,
            uptime_seconds=time.time() - psutil.boot_time()
        )
    except ImportError:
        logger.warning("psutil not installed, skipping system health check")
        system_health = SystemHealth(
            cpu_percent=0.0,
            memory_percent=0.0,
            uptime_seconds=0.0
        )
    except Exception as e:
        logger.error(f"System health check failed: {e}")
        overall_status = "degraded"
        system_health = SystemHealth(
            cpu_percent=0.0,
            memory_percent=0.0,
            uptime_seconds=0.0
        )
    
    # Provider health (basic checks)
    providers = {}
    
    # Check OpenRouter
    if settings.openrouter_enabled:
        providers["openrouter"] = "configured"
    else:
        providers["openrouter"] = "not_configured"
    
    # Check Cloudflare
    if settings.cloudflare_enabled:
        providers["cloudflare"] = "configured"
    else:
        providers["cloudflare"] = "not_configured"
    
    # Check Bedrock
    if settings.bedrock_enabled:
        providers["bedrock"] = "configured"
    else:
        providers["bedrock"] = "not_configured"
    
    # Determine final status
    if overall_status == "healthy":
        # All critical services are healthy
        pass
    elif overall_status == "degraded":
        # Some non-critical services have issues
        if db_health["status"] == "unhealthy" or redis_health["status"] == "unhealthy":
            overall_status = "unhealthy"
    
    return DetailedHealthResponse(
        overall_status=overall_status,
        api=api_health,
        database=database_health,
        redis=redis_detailed,
        system=system_health,
        providers=providers
    )


# Readiness check (for Kubernetes)
async def readiness_check() -> Dict[str, str]:
    """Readiness check for container orchestration"""
    
    try:
        # Check database
        db_status = await db_health_check()
        if db_status["status"] != "healthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not ready"
            )
        
        # Check Redis
        redis_status = await redis_health_check()
        if redis_status["status"] != "healthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis not ready"
            )
        
        return {
            "status": "ready",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {str(e)}"
        )


# Liveness check (for Kubernetes)
async def liveness_check() -> Dict[str, str]:
    """Liveness check for container orchestration"""
    
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "pid": str(asyncio.get_running_loop())
    }


# Component-specific health checks
async def database_health() -> Dict[str, Any]:
    """Database-specific health check"""
    return await db_health_check()


async def redis_health_endpoint() -> Dict[str, Any]:
    """Redis-specific health check"""
    return await redis_health_check()


# Health check with custom timeout
async def health_with_timeout(timeout_seconds: int = 30) -> Dict[str, Any]:
    """Health check with custom timeout"""
    
    try:
        # Run health checks with timeout
        health_result = await asyncio.wait_for(
            detailed_health(),
            timeout=timeout_seconds
        )
        
        return health_result.dict()
        
    except asyncio.TimeoutError:
        logger.error(f"Health check timed out after {timeout_seconds} seconds")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"Health check timed out after {timeout_seconds} seconds"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


# Health check endpoint with metrics
async def health_with_metrics() -> Dict[str, Any]:
    """Health check with additional metrics"""
    
    base_health = await detailed_health()
    
    # Add some basic metrics
    metrics = {
        "active_connections": getattr(base_health, '_active_connections', 0),
        "queue_size": getattr(base_health, '_queue_size', 0),
        "error_rate_5m": getattr(base_health, '_error_rate_5m', 0.0),
        "avg_response_time_ms": getattr(base_health, '_avg_response_time_ms', 0.0),
    }
    
    # Convert to dict and add metrics
    health_dict = base_health.dict()
    health_dict["metrics"] = metrics
    
    return health_dict


# Create router
from fastapi import APIRouter

router = APIRouter()

# Add routes
router.add_api_route(
    "/health",
    simple_health,
    methods=["GET"],
    tags=["Health"],
    summary="Simple health check"
)

router.add_api_route(
    "/health/detailed",
    detailed_health,
    methods=["GET"],
    tags=["Health"],
    summary="Detailed health check"
)

router.add_api_route(
    "/health/readiness",
    readiness_check,
    methods=["GET"],
    tags=["Health"],
    summary="Readiness check"
)

router.add_api_route(
    "/health/liveness",
    liveness_check,
    methods=["GET"],
    tags=["Health"],
    summary="Liveness check"
)

router.add_api_route(
    "/health/database",
    database_health,
    methods=["GET"],
    tags=["Health"],
    summary="Database health check"
)

router.add_api_route(
    "/health/redis",
    redis_health_endpoint,
    methods=["GET"],
    tags=["Health"],
    summary="Redis health check"
)

router.add_api_route(
    "/health/timeout",
    health_with_timeout,
    methods=["GET"],
    tags=["Health"],
    summary="Health check with timeout"
)

router.add_api_route(
    "/health/metrics",
    health_with_metrics,
    methods=["GET"],
    tags=["Health"],
    summary="Health check with metrics"
)


# Legacy health endpoint for backward compatibility
@router.get("/", include_in_schema=False)
async def root_health():
    """Root health endpoint (legacy)"""
    return await simple_health()