"""
Billing service for bl1nk-agent-builder
Handles usage tracking and billing
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BillingService:
    """Service for handling billing and usage tracking"""
    
    def __init__(self):
        self.usage_logs = []  # In-memory (would use database in production)
    
    async def log_usage(
        self,
        user_id: str,
        task_id: int,
        provider: str,
        model: str,
        tokens_input: int,
        tokens_output: int,
        cost_usd: float
    ):
        """Log usage for billing"""
        
        usage_record = {
            "id": len(self.usage_logs) + 1,
            "user_id": user_id,
            "task_id": task_id,
            "provider": provider,
            "model": model,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "cost_usd": cost_usd,
            "created_at": datetime.now()
        }
        
        self.usage_logs.append(usage_record)
        
        logger.info(
            "Usage logged",
            extra={
                "event": "usage_logged",
                "user_id": user_id,
                "task_id": task_id,
                "provider": provider,
                "cost_usd": cost_usd
            }
        )
    
    async def get_user_usage(
        self, 
        user_id: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """Get usage statistics for user"""
        
        # Filter usage logs for user and timeframe
        cutoff_date = datetime.now() - timedelta(days=days)
        
        user_logs = [
            log for log in self.usage_logs 
            if log["user_id"] == user_id and log["created_at"] >= cutoff_date
        ]
        
        total_cost = sum(log["cost_usd"] for log in user_logs)
        total_tokens = sum(log["tokens_input"] + log["tokens_output"] for log in user_logs)
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_requests": len(user_logs),
            "total_cost_usd": total_cost,
            "total_tokens": total_tokens,
            "average_cost_per_request": total_cost / len(user_logs) if user_logs else 0
        }