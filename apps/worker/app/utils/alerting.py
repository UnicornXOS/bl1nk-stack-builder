"""
Alerting utilities for bl1nk-agent-builder
Handles system alerts and notifications
"""

import logging
from enum import Enum
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertingService:
    """Service for sending alerts"""
    
    async def send_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        metadata: Dict[str, Any] = None
    ):
        """Send alert notification"""
        
        logger.warning(
            f"ALERT [{severity.value.upper()}]: {title} - {message}",
            extra={
                "event": "alert_sent",
                "severity": severity.value,
                "title": title,
                "message": message,
                "metadata": metadata or {}
            }
        )