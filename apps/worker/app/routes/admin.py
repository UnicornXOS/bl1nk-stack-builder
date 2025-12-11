"""
Admin endpoints for bl1nk-agent-builder
Provides administrative functionality for system management
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.middleware.auth import get_current_admin_user

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Pydantic models
class SystemStats(BaseModel):
    """System statistics model"""
    total_users: int
    total_tasks: int
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_skills: int
    total_mcp_tools: int
    uptime_hours: float
    memory_usage_mb: float
    cpu_usage_percent: float


class UserStats(BaseModel):
    """User statistics model"""
    user_id: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_cost: float
    last_activity: Optional[str] = None


class ProviderStats(BaseModel):
    """Provider statistics model"""
    provider: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_cost: float
    avg_response_time_ms: float


class TaskAnalytics(BaseModel):
    """Task analytics model"""
    date: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    avg_processing_time_seconds: float
    total_cost: float


router = APIRouter()

# In-memory analytics data (in production, this would be from database)
analytics_data = {
    "users": {},
    "tasks": {},
    "providers": {},
    "system_stats": SystemStats(
        total_users=100,
        total_tasks=1000,
        active_tasks=10,
        completed_tasks=950,
        failed_tasks=40,
        total_skills=5,
        total_mcp_tools=3,
        uptime_hours=72.5,
        memory_usage_mb=512.3,
        cpu_usage_percent=15.7
    )
}

@router.get("/admin/stats/system", response_model=SystemStats)
async def get_system_stats(current_user: str = Depends(get_current_admin_user)):
    """Get system-wide statistics"""
    
    try:
        # In production, this would query the database
        stats = analytics_data["system_stats"]
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system statistics"
        )


@router.get("/admin/stats/users", response_model=List[UserStats])
async def get_user_stats(
    limit: int = 100,
    offset: int = 0,
    current_user: str = Depends(get_current_admin_user)
):
    """Get user statistics"""
    
    try:
        # Return mock data for now
        users = []
        for i in range(offset, min(offset + limit, 10)):
            user_stats = UserStats(
                user_id=f"user_{i:03d}",
                total_tasks=50 + i * 10,
                completed_tasks=45 + i * 9,
                failed_tasks=5 + i,
                total_cost=25.50 + i * 5.25,
                last_activity=(datetime.now() - timedelta(hours=i)).isoformat()
            )
            users.append(user_stats)
        
        return users
        
    except Exception as e:
        logger.error(f"Failed to get user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )


@router.get("/admin/stats/providers", response_model=List[ProviderStats])
async def get_provider_stats(current_user: str = Depends(get_current_admin_user)):
    """Get provider statistics"""
    
    try:
        # Return mock data for now
        providers = [
            ProviderStats(
                provider="openrouter",
                total_requests=500,
                successful_requests=480,
                failed_requests=20,
                total_cost=125.75,
                avg_response_time_ms=850.3
            ),
            ProviderStats(
                provider="cloudflare",
                total_requests=300,
                successful_requests=295,
                failed_requests=5,
                total_cost=75.25,
                avg_response_time_ms=620.1
            ),
            ProviderStats(
                provider="bedrock",
                total_requests=200,
                successful_requests=195,
                failed_requests=5,
                total_cost=150.00,
                avg_response_time_ms=1200.5
            )
        ]
        
        return providers
        
    except Exception as e:
        logger.error(f"Failed to get provider stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve provider statistics"
        )


@router.get("/admin/analytics/tasks", response_model=List[TaskAnalytics])
async def get_task_analytics(
    days: int = 7,
    current_user: str = Depends(get_current_admin_user)
):
    """Get task analytics for the last N days"""
    
    try:
        analytics = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            analytics.append(TaskAnalytics(
                date=date,
                total_tasks=100 + i * 10,
                completed_tasks=95 + i * 9,
                failed_tasks=5 + i,
                avg_processing_time_seconds=2.5 + i * 0.1,
                total_cost=50.25 + i * 5.25
            ))
        
        return analytics
        
    except Exception as e:
        logger.error(f"Failed to get task analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve task analytics"
        )


@router.get("/admin/health/detailed")
async def admin_health_check(current_user: str = Depends(get_current_admin_user)):
    """Detailed health check for admin users"""
    
    try:
        # This would include more detailed system information
        # that regular users shouldn't see
        
        import psutil
        
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "uptime_hours": (datetime.now() - datetime.fromtimestamp(psutil.boot_time())).total_seconds() / 3600
            },
            "database": {
                "status": "healthy",  # Would check actual DB connection
                "connections": 5,
                "queries_per_second": 10.5
            },
            "redis": {
                "status": "healthy",  # Would check actual Redis connection
                "connected_clients": 3,
                "used_memory_mb": 12.5
            },
            "providers": {
                "openrouter": {"status": "healthy", "last_check": datetime.now().isoformat()},
                "cloudflare": {"status": "healthy", "last_check": datetime.now().isoformat()},
                "bedrock": {"status": "healthy", "last_check": datetime.now().isoformat()}
            }
        }
        
        return health_data
        
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System monitoring tools not available"
        )
    except Exception as e:
        logger.error(f"Failed to get admin health check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve detailed health information"
        )


@router.post("/admin/maintenance/enable")
async def enable_maintenance_mode(
    reason: str,
    current_user: str = Depends(get_current_admin_user)
):
    """Enable maintenance mode"""
    
    logger.warning(f"Maintenance mode enabled by {current_user}: {reason}")
    
    # In production, this would:
    # 1. Set a flag in the database
    # 2. Return 503 for new requests
    # 3. Allow existing requests to complete
    
    return {
        "message": "Maintenance mode enabled",
        "reason": reason,
        "enabled_by": current_user,
        "enabled_at": datetime.now().isoformat()
    }


@router.post("/admin/maintenance/disable")
async def disable_maintenance_mode(current_user: str = Depends(get_current_admin_user)):
    """Disable maintenance mode"""
    
    logger.info(f"Maintenance mode disabled by {current_user}")
    
    return {
        "message": "Maintenance mode disabled",
        "disabled_by": current_user,
        "disabled_at": datetime.now().isoformat()
    }


@router.get("/admin/logs/recent")
async def get_recent_logs(
    lines: int = 100,
    level: Optional[str] = None,
    current_user: str = Depends(get_current_admin_user)
):
    """Get recent application logs"""
    
    # In production, this would read from actual log files
    # For now, return mock data
    
    mock_logs = [
        {
            "timestamp": (datetime.now() - timedelta(minutes=i)).isoformat(),
            "level": "INFO",
            "message": f"Application log entry {i}",
            "module": "app.main",
            "trace_id": f"trace_{i:08d}"
        }
        for i in range(lines)
    ]
    
    if level:
        mock_logs = [log for log in mock_logs if log["level"] == level.upper()]
    
    return {
        "logs": mock_logs,
        "total": len(mock_logs),
        "level_filter": level,
        "lines_requested": lines
    }


@router.get("/admin/users/{user_id}/activity")
async def get_user_activity(
    user_id: str,
    days: int = 7,
    current_user: str = Depends(get_current_admin_user)
):
    """Get detailed activity for a specific user"""
    
    # In production, this would query the database for user activity
    # For now, return mock data
    
    activities = []
    for i in range(20):
        activities.append({
            "timestamp": (datetime.now() - timedelta(hours=i)).isoformat(),
            "action": "task_created" if i % 2 == 0 else "task_completed",
            "details": {
                "task_id": f"task_{i:03d}",
                "task_type": "chat" if i % 3 == 0 else "embedding"
            }
        })
    
    return {
        "user_id": user_id,
        "activities": activities,
        "total_activities": len(activities),
        "period_days": days
    }


@router.post("/admin/users/{user_id}/disable")
async def disable_user(
    user_id: str,
    reason: str,
    current_user: str = Depends(get_current_admin_user)
):
    """Disable a user account"""
    
    logger.warning(f"User {user_id} disabled by {current_user}: {reason}")
    
    # In production, this would:
    # 1. Update user status in database
    # 2. Revoke active tokens
    # 3. Stop processing their tasks
    
    return {
        "message": f"User {user_id} has been disabled",
        "reason": reason,
        "disabled_by": current_user,
        "disabled_at": datetime.now().isoformat()
    }


@router.post("/admin/users/{user_id}/enable")
async def enable_user(user_id: str, current_user: str = Depends(get_current_admin_user)):
    """Enable a user account"""
    
    logger.info(f"User {user_id} enabled by {current_user}")
    
    return {
        "message": f"User {user_id} has been enabled",
        "enabled_by": current_user,
        "enabled_at": datetime.now().isoformat()
    }