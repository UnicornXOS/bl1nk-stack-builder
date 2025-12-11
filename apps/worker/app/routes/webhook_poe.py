"""
Poe webhook handler for bl1nk-agent-builder
Handles incoming webhooks from Poe platform
"""

import logging
import hashlib
import hmac
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from jose import jwt

from app.utils.tracing import get_trace_id
from app.utils.idempotency import get_or_create_task
from app.middleware.auth import get_current_user

logger = logging.getLogger(__name__)


# Pydantic models
class PoeWebhookPayload(BaseModel):
    """Poe webhook payload model"""
    source: str = Field(default="poe")
    external_id: str = Field(..., description="Unique ID from Poe")
    user_id: str = Field(..., description="User ID")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    message: str = Field(..., description="User message")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "source": "poe",
                "external_id": "poe_123456789",
                "user_id": "user_abc123",
                "conversation_id": "conv_xyz789",
                "message": "Hello, how can you help me?",
                "metadata": {
                    "platform": "poe",
                    "user_agent": "Poe/1.0",
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            }
        }


class PoeAckResponse(BaseModel):
    """Poe webhook acknowledgment response"""
    status: str = Field(default="accepted")
    task_id: int = Field(..., description="Internal task ID")
    message: str = Field(default="Task accepted for processing")


async def verify_poe_signature(request: Request, payload: bytes) -> bool:
    """Verify Poe webhook signature"""
    
    # Get signature from headers
    signature = request.headers.get("X-Poe-Signature") or request.headers.get("X-Signature")
    
    if not signature:
        logger.warning("No Poe signature found in headers")
        return False
    
    # Get webhook secret from environment (if configured)
    webhook_secret = "poe_webhook_secret"  # This should come from settings
    
    if not webhook_secret:
        logger.warning("No Poe webhook secret configured")
        return False
    
    # Calculate expected signature
    expected_signature = hmac.new(
        webhook_secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    return hmac.compare_digest(signature, expected_signature)


async def process_poe_webhook(payload: PoeWebhookPayload, request: Request) -> PoeAckResponse:
    """Process Poe webhook payload"""
    
    trace_id = get_trace_id(request)
    
    try:
        # Validate required fields
        if not payload.external_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="external_id is required"
            )
        
        if not payload.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id is required"
            )
        
        if not payload.message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="message is required"
            )
        
        logger.info(
            f"Processing Poe webhook - external_id: {payload.external_id}, user_id: {payload.user_id}",
            extra={
                "event": "webhook_received",
                "source": "poe",
                "external_id": payload.external_id,
                "user_id": payload.user_id,
                "trace_id": trace_id
            }
        )
        
        # Use idempotency to get or create task
        task_id = await get_or_create_task(
            source="poe",
            external_id=payload.external_id,
            payload={
                "user_id": payload.user_id,
                "conversation_id": payload.conversation_id,
                "message": payload.message,
                "metadata": payload.metadata,
                "trace_id": trace_id
            }
        )
        
        # Enqueue task for processing
        # This would typically add the task to a queue for background processing
        from app.database.redis import enqueue_task
        
        task_data = {
            "task_id": task_id,
            "type": "poe_chat",
            "source": "poe",
            "external_id": payload.external_id,
            "user_id": payload.user_id,
            "conversation_id": payload.conversation_id,
            "message": payload.message,
            "metadata": payload.metadata,
            "trace_id": trace_id,
            "created_at": datetime.now().isoformat()
        }
        
        await enqueue_task(task_data, priority=1)  # Priority 1 for chat tasks
        
        logger.info(
            f"Poe webhook processed successfully - task_id: {task_id}",
            extra={
                "event": "webhook_processed",
                "source": "poe",
                "task_id": task_id,
                "external_id": payload.external_id,
                "trace_id": trace_id
            }
        )
        
        return PoeAckResponse(
            status="accepted",
            task_id=task_id,
            message=f"Task {task_id} accepted for processing"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to process Poe webhook: {e}",
            extra={
                "event": "webhook_error",
                "source": "poe",
                "external_id": payload.external_id,
                "trace_id": trace_id,
                "error": str(e)
            },
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )


# FastAPI router
from fastapi import APIRouter

router = APIRouter()


@router.post(
    "/webhook/poe",
    response_model=PoeAckResponse,
    status_code=status.HTTP_200_OK,
    tags=["Webhooks"],
    summary="Poe webhook receiver",
    description="""
    Receive webhooks from Poe platform.
    
    This endpoint handles incoming chat messages from Poe and creates
    tasks for processing. The webhook includes:
    - External ID for idempotency
    - User ID and conversation ID
    - Message content
    - Optional metadata
    
    The response includes a task ID that can be used to track progress.
    """
)
async def poe_webhook_handler(
    request: Request,
    # Note: In production, you might want to use raw body for signature verification
    payload: PoeWebhookPayload = Depends()
):
    """Handle incoming Poe webhooks"""
    
    # Verify signature (optional, depends on Poe's webhook configuration)
    if settings.poe_webhook_secret:
        try:
            body = await request.body()
            if not await verify_poe_signature(request, body):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid signature"
                )
        except Exception as e:
            logger.warning(f"Signature verification failed: {e}")
            # Continue processing if signature verification fails
    
    # Process the webhook
    result = await process_poe_webhook(payload, request)
    
    return result


# Additional utility endpoints for Poe integration
@router.get(
    "/webhook/poe/test",
    status_code=status.HTTP_200_OK,
    tags=["Webhooks"],
    summary="Poe webhook test endpoint",
    description="Test endpoint to verify Poe webhook connectivity"
)
async def poe_webhook_test():
    """Test Poe webhook connectivity"""
    return {
        "status": "ok",
        "service": "bl1nk-agent-builder",
        "webhook": "poe",
        "timestamp": datetime.now().isoformat()
    }


@router.post(
    "/webhook/poe/verify",
    status_code=status.HTTP_200_OK,
    tags=["Webhooks"],
    summary="Verify Poe webhook signature",
    description="Verify a Poe webhook signature without processing the webhook"
)
async def poe_webhook_verify(
    request: Request,
    signature: str,
    body: str
):
    """Verify Poe webhook signature"""
    
    try:
        # Calculate expected signature
        if not settings.poe_webhook_secret:
            return {
                "valid": False,
                "error": "No webhook secret configured"
            }
        
        expected_signature = hmac.new(
            settings.poe_webhook_secret.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        is_valid = hmac.compare_digest(signature, expected_signature)
        
        return {
            "valid": is_valid,
            "provided_signature": signature,
            "expected_signature": expected_signature,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signature verification failed: {str(e)}"
        )


# Add Poe-specific settings validation
def validate_poe_config():
    """Validate Poe configuration"""
    issues = []
    
    if not hasattr(settings, 'poe_webhook_secret') or not settings.poe_webhook_secret:
        issues.append("Poe webhook secret not configured")
    
    # Add more validation as needed
    
    if issues:
        logger.warning(f"Poe configuration issues: {issues}")
    
    return issues


# Initialize Poe webhook handler
def setup_poe_webhook():
    """Setup Poe webhook handler"""
    logger.info("Setting up Poe webhook handler")
    
    # Validate configuration
    issues = validate_poe_config()
    if issues:
        logger.warning(f"Poe webhook configuration issues: {issues}")
    
    logger.info("Poe webhook handler configured successfully")


# Export setup function
__all__ = ["router", "setup_poe_webhook"]