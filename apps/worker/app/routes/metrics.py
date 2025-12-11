"""
Metrics endpoints for bl1nk-agent-builder
Provides Prometheus-compatible metrics
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, status, Query
from fastapi.responses import Response, PlainTextResponse
from pydantic import BaseModel

from app.database.connection import fetch_val, fetch_many
from app.database.redis import get_redis
from app.config.settings import settings

logger = logging.getLogger(__name__)


# Prometheus metric counters and gauges
class MetricsCollector:
    """Collect and expose application metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.active_connections = 0
        
    def increment_request_count(self):
        """Increment request counter"""
        self.request_count += 1
        
    def increment_error_count(self):
        """Increment error counter"""
        self.error_count += 1
        
    def set_active_connections(self, count: int):
        """Set active connections gauge"""
        self.active_connections = count
        
    def get_uptime_seconds(self) -> float:
        """Get application uptime in seconds"""
        return time.time() - self.start_time


# Global metrics collector
metrics_collector = MetricsCollector()


# Pydantic models for metrics responses
class MetricsSummary(BaseModel):
    timestamp: datetime
    uptime_seconds: float
    request_count: int
    error_count: int
    error_rate: float
    active_connections: int
    queue_length: int
    database_status: str
    redis_status: str


class ProviderMetrics(BaseModel):
    provider: str
    requests_total: int
    errors_total: int
    avg_latency_ms: float
    cost_usd: float


class TaskMetrics(BaseModel):
    total_tasks: int
    pending_tasks: int
    processing_tasks: int
    completed_tasks: int
    failed_tasks: int
    avg_processing_time_seconds: float


async def get_basic_metrics() -> MetricsSummary:
    """Get basic application metrics"""
    
    try:
        # Calculate uptime
        uptime_seconds = metrics_collector.get_uptime_seconds()
        
        # Get queue length from Redis
        redis = get_redis()
        queue_length = await redis.llen(settings.task_queue_name)
        
        # Calculate error rate
        error_rate = 0.0
        if metrics_collector.request_count > 0:
            error_rate = (metrics_collector.error_count / metrics_collector.request_count) * 100
        
        # Get database status (simplified)
        try:
            db_status = await fetch_val("SELECT 1")
            database_status = "healthy" if db_status == 1 else "unhealthy"
        except Exception:
            database_status = "error"
        
        # Get Redis status (simplified)
        try:
            redis = get_redis()
            await redis.ping()
            redis_status = "healthy"
        except Exception:
            redis_status = "error"
        
        return MetricsSummary(
            timestamp=datetime.now(),
            uptime_seconds=uptime_seconds,
            request_count=metrics_collector.request_count,
            error_count=metrics_collector.error_count,
            error_rate=error_rate,
            active_connections=metrics_collector.active_connections,
            queue_length=queue_length,
            database_status=database_status,
            redis_status=redis_status
        )
        
    except Exception as e:
        logger.error(f"Failed to collect basic metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect metrics: {str(e)}"
        )


async def get_task_metrics() -> TaskMetrics:
    """Get task-related metrics"""
    
    try:
        # Get task counts from database
        total_tasks = await fetch_val("SELECT COUNT(*) FROM tasks")
        pending_tasks = await fetch_val("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
        processing_tasks = await fetch_val("SELECT COUNT(*) FROM tasks WHERE status = 'processing'")
        completed_tasks = await fetch_val("SELECT COUNT(*) FROM tasks WHERE status = 'completed'")
        failed_tasks = await fetch_val("SELECT COUNT(*) FROM tasks WHERE status = 'failed'")
        
        # Get average processing time (last 100 completed tasks)
        avg_processing_time = await fetch_val("""
            SELECT AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) 
            FROM tasks 
            WHERE status = 'completed' 
            ORDER BY updated_at DESC 
            LIMIT 100
        """)
        
        return TaskMetrics(
            total_tasks=total_tasks or 0,
            pending_tasks=pending_tasks or 0,
            processing_tasks=processing_tasks or 0,
            completed_tasks=completed_tasks or 0,
            failed_tasks=failed_tasks or 0,
            avg_processing_time_seconds=float(avg_processing_time or 0)
        )
        
    except Exception as e:
        logger.error(f"Failed to collect task metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect task metrics: {str(e)}"
        )


async def get_provider_metrics() -> list[ProviderMetrics]:
    """Get provider-related metrics"""
    
    try:
        # Get provider usage from usage_logs table
        usage_data = await fetch_many("""
            SELECT 
                provider,
                COUNT(*) as requests_total,
                SUM(CASE WHEN cost_usd > 0 THEN 1 ELSE 0 END) as errors_total,
                AVG(cost_usd) as avg_cost,
                SUM(cost_usd) as total_cost
            FROM usage_logs 
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            GROUP BY provider
        """)
        
        metrics = []
        for row in usage_data:
            metrics.append(ProviderMetrics(
                provider=row['provider'],
                requests_total=int(row['requests_total']),
                errors_total=int(row['errors_total']),
                avg_latency_ms=0.0,  # Would need to track this separately
                cost_usd=float(row['total_cost'] or 0)
            ))
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to collect provider metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect provider metrics: {str(e)}"
        )


async def get_system_metrics() -> Dict[str, Any]:
    """Get system-level metrics"""
    
    try:
        import psutil
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_used_gb = disk.used / (1024**3)
        disk_total_gb = disk.total / (1024**3)
        
        # Network metrics
        network = psutil.net_io_counters()
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "load_avg": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            },
            "memory": {
                "percent": memory_percent,
                "used_gb": memory_used_gb,
                "total_gb": memory_total_gb
            },
            "disk": {
                "percent": disk_percent,
                "used_gb": disk_used_gb,
                "total_gb": disk_total_gb
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
        }
        
    except ImportError:
        logger.warning("psutil not installed, skipping system metrics")
        return {
            "cpu": {"percent": 0.0, "count": 1},
            "memory": {"percent": 0.0, "used_gb": 0.0, "total_gb": 0.0},
            "disk": {"percent": 0.0, "used_gb": 0.0, "total_gb": 0.0},
            "network": {"bytes_sent": 0, "bytes_recv": 0, "packets_sent": 0, "packets_recv": 0}
        }
    except Exception as e:
        logger.error(f"Failed to collect system metrics: {e}")
        return {
            "error": str(e),
            "cpu": {"percent": 0.0, "count": 0},
            "memory": {"percent": 0.0, "used_gb": 0.0, "total_gb": 0.0},
            "disk": {"percent": 0.0, "used_gb": 0.0, "total_gb": 0.0},
            "network": {"bytes_sent": 0, "bytes_recv": 0, "packets_sent": 0, "packets_recv": 0}
        }


def generate_prometheus_metrics() -> str:
    """Generate Prometheus-formatted metrics"""
    
    uptime_seconds = metrics_collector.get_uptime_seconds()
    error_rate = 0.0
    if metrics_collector.request_count > 0:
        error_rate = (metrics_collector.error_count / metrics_collector.request_count) * 100
    
    # Start building Prometheus output
    metrics = []
    
    # Help text
    metrics.append("# HELP bl1nk_uptime_seconds Application uptime in seconds")
    metrics.append("# TYPE bl1nk_uptime_seconds counter")
    metrics.append(f"bl1nk_uptime_seconds {uptime_seconds}")
    
    metrics.append("# HELP bl1nk_requests_total Total number of requests")
    metrics.append("# TYPE bl1nk_requests_total counter")
    metrics.append(f"bl1nk_requests_total {metrics_collector.request_count}")
    
    metrics.append("# HELP bl1nk_errors_total Total number of errors")
    metrics.append("# TYPE bl1nk_errors_total counter")
    metrics.append(f"bl1nk_errors_total {metrics_collector.error_count}")
    
    metrics.append("# HELP bl1nk_error_rate Error rate percentage")
    metrics.append("# TYPE bl1nk_error_rate gauge")
    metrics.append(f"bl1nk_error_rate {error_rate}")
    
    metrics.append("# HELP bl1nk_active_connections Current active connections")
    metrics.append("# TYPE bl1nk_active_connections gauge")
    metrics.append(f"bl1nk_active_connections {metrics_collector.active_connections}")
    
    # Add timestamp
    timestamp = int(time.time())
    metrics.append(f"# Generated at {datetime.fromtimestamp(timestamp).isoformat()}")
    
    return "\n".join(metrics)


# FastAPI routes
from fastapi import APIRouter

router = APIRouter()


@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    try:
        metrics_output = generate_prometheus_metrics()
        return PlainTextResponse(metrics_output, media_type="text/plain")
    except Exception as e:
        logger.error(f"Failed to generate Prometheus metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate metrics: {str(e)}"
        )


@router.get("/metrics/summary")
async def metrics_summary():
    """JSON metrics summary"""
    return await get_basic_metrics()


@router.get("/metrics/tasks")
async def metrics_tasks():
    """Task-related metrics"""
    return await get_task_metrics()


@router.get("/metrics/providers")
async def metrics_providers():
    """Provider-related metrics"""
    return await get_provider_metrics()


@router.get("/metrics/system")
async def metrics_system():
    """System-level metrics"""
    return await get_system_metrics()


@router.get("/metrics/all")
async def metrics_all():
    """All metrics combined"""
    try:
        basic_metrics = await get_basic_metrics()
        task_metrics = await get_task_metrics()
        provider_metrics = await get_provider_metrics()
        system_metrics = await get_system_metrics()
        
        return {
            "basic": basic_metrics.dict(),
            "tasks": task_metrics.dict(),
            "providers": [m.dict() for m in provider_metrics],
            "system": system_metrics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to collect all metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect all metrics: {str(e)}"
        )


# Utility functions for internal use
def increment_request_counter():
    """Increment request counter (for internal use)"""
    metrics_collector.increment_request_count()


def increment_error_counter():
    """Increment error counter (for internal use)"""
    metrics_collector.increment_error_count()


def set_active_connections_gauge(count: int):
    """Set active connections gauge (for internal use)"""
    metrics_collector.set_active_connections(count)