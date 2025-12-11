"""
Idempotency utilities for bl1nk-agent-builder
Ensures that duplicate requests don't create duplicate operations
"""

import logging
import hashlib
import json
from typing import Optional, Dict, Any, Tuple

from app.database.connection import fetch_one, execute_query
from app.config.settings import settings

logger = logging.getLogger(__name__)


async def get_or_create_task(
    source: str, 
    external_id: str, 
    payload: Dict[str, Any]
) -> int:
    """
    Get existing task or create new one based on source and external_id.
    This ensures idempotency for webhook requests.
    
    Args:
        source: The source platform (poe, manus, slack, etc.)
        external_id: Unique ID from the source platform
        payload: Task payload data
    
    Returns:
        Task ID (existing or newly created)
    """
    
    try:
        # Check for existing task
        existing_task = await fetch_one(
            "SELECT id FROM tasks WHERE source = $1 AND external_id = $2",
            source,
            external_id
        )
        
        if existing_task:
            logger.debug(
                f"Found existing task for {source}:{external_id} - ID: {existing_task['id']}"
            )
            return existing_task['id']
        
        # Create new task
        task_id = await execute_query(
            """
            INSERT INTO tasks (
                source, 
                external_id, 
                input_payload, 
                status,
                created_at,
                updated_at
            ) VALUES ($1, $2, $3, 'pending', NOW(), NOW())
            RETURNING id
            """,
            source,
            external_id,
            json.dumps(payload)
        )
        
        # Extract ID from result
        # execute_query returns string like "INSERT 0 123"
        if isinstance(task_id, str) and " " in task_id:
            task_id = int(task_id.split()[-1])
        elif isinstance(task_id, int):
            pass
        else:
            raise ValueError(f"Unexpected task_id format: {task_id}")
        
        logger.info(
            f"Created new task for {source}:{external_id} - ID: {task_id}"
        )
        
        return task_id
        
    except Exception as e:
        logger.error(f"Failed to get or create task: {e}")
        raise


async def check_idempotency_key(
    operation_type: str,
    idempotency_key: str,
    payload: Dict[str, Any]
) -> Tuple[bool, Optional[str]]:
    """
    Check if an operation with the given idempotency key has been processed.
    
    Args:
        operation_type: Type of operation (e.g., 'task_create', 'skill_invoke')
        idempotency_key: Unique key for the operation
        payload: Operation payload
    
    Returns:
        Tuple of (is_duplicate, result_data)
        - is_duplicate: True if this operation was already processed
        - result_data: Result data if duplicate, None if new operation
    """
    
    try:
        # Create a hash of the payload for storage
        payload_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()
        
        # Check for existing idempotency record
        existing = await fetch_one(
            """
            SELECT result_data, payload_hash 
            FROM idempotency_keys 
            WHERE operation_type = $1 AND idempotency_key = $2
            """,
            operation_type,
            idempotency_key
        )
        
        if existing:
            # Verify payload hash matches
            if existing['payload_hash'] == payload_hash:
                logger.debug(
                    f"Found duplicate operation: {operation_type}:{idempotency_key}"
                )
                return True, json.loads(existing['result_data'])
            else:
                logger.warning(
                    f"Idempotency key {idempotency_key} exists with different payload"
                )
                raise ValueError("Idempotency key exists with different payload")
        
        return False, None
        
    except Exception as e:
        logger.error(f"Failed to check idempotency: {e}")
        raise


async def store_idempotency_result(
    operation_type: str,
    idempotency_key: str,
    payload: Dict[str, Any],
    result_data: Dict[str, Any],
    ttl_seconds: int = 86400  # 24 hours default
) -> None:
    """
    Store the result of an idempotent operation.
    
    Args:
        operation_type: Type of operation
        idempotency_key: Unique key for the operation
        payload: Operation payload
        result_data: Result data to store
        ttl_seconds: Time to live in seconds
    """
    
    try:
        payload_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()
        
        await execute_query(
            """
            INSERT INTO idempotency_keys (
                operation_type,
                idempotency_key,
                payload_hash,
                result_data,
                created_at,
                expires_at
            ) VALUES ($1, $2, $3, $4, NOW(), NOW() + INTERVAL '%s seconds')
            ON CONFLICT (operation_type, idempotency_key) 
            DO UPDATE SET 
                payload_hash = $3,
                result_data = $4,
                updated_at = NOW(),
                expires_at = NOW() + INTERVAL '%s seconds'
            """,
            operation_type,
            idempotency_key,
            payload_hash,
            json.dumps(result_data),
            ttl_seconds,
            ttl_seconds
        )
        
        logger.debug(
            f"Stored idempotency result: {operation_type}:{idempotency_key}"
        )
        
    except Exception as e:
        logger.error(f"Failed to store idempotency result: {e}")
        raise


async def cleanup_expired_idempotency_keys() -> int:
    """
    Clean up expired idempotency keys.
    
    Returns:
        Number of records cleaned up
    """
    
    try:
        result = await execute_query(
            """
            DELETE FROM idempotency_keys 
            WHERE expires_at < NOW()
            """
        )
        
        # Extract count from result
        if isinstance(result, str) and " " in result:
            deleted_count = int(result.split()[-1])
        else:
            deleted_count = 0
        
        logger.info(f"Cleaned up {deleted_count} expired idempotency keys")
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired idempotency keys: {e}")
        raise


# Utility functions for specific operations

async def get_or_create_webhook_task(
    source: str,
    external_id: str,
    user_id: str,
    message: str,
    metadata: Dict[str, Any] = None
) -> int:
    """
    Convenience function for webhook tasks.
    
    Args:
        source: Webhook source (poe, manus, slack)
        external_id: External ID from source
        user_id: User ID
        message: User message
        metadata: Additional metadata
    
    Returns:
        Task ID
    """
    
    payload = {
        "user_id": user_id,
        "message": message,
        "metadata": metadata or {}
    }
    
    return await get_or_create_task(source, external_id, payload)


async def check_skill_invocation_idempotency(
    skill_id: str,
    request_id: str,
    inputs: Dict[str, Any]
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Check if a skill invocation has already been processed.
    
    Args:
        skill_id: ID of the skill
        request_id: Request ID for idempotency
        inputs: Skill inputs
    
    Returns:
        Tuple of (is_duplicate, result)
    """
    
    operation_type = f"skill_invoke_{skill_id}"
    
    return await check_idempotency_key(
        operation_type=operation_type,
        idempotency_key=request_id,
        payload=inputs
    )


async def store_skill_invocation_result(
    skill_id: str,
    request_id: str,
    inputs: Dict[str, Any],
    result: Dict[str, Any]
) -> None:
    """
    Store the result of a skill invocation for idempotency.
    
    Args:
        skill_id: ID of the skill
        request_id: Request ID
        inputs: Skill inputs
        result: Invocation result
    """
    
    operation_type = f"skill_invoke_{skill_id}"
    
    await store_idempotency_result(
        operation_type=operation_type,
        idempotency_key=request_id,
        payload=inputs,
        result_data=result,
        ttl_seconds=3600  # 1 hour for skill invocations
    )


# Database schema for idempotency (add to migrations if not exists)
IDEMPOTENCY_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS idempotency_keys (
    id BIGSERIAL PRIMARY KEY,
    operation_type TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    result_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    UNIQUE(operation_type, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_idempotency_keys_expires_at 
    ON idempotency_keys(expires_at);

CREATE INDEX IF NOT EXISTS idx_idempotency_keys_operation_type 
    ON idempotency_keys(operation_type);
"""


async def create_idempotency_table():
    """Create idempotency table if it doesn't exist"""
    
    try:
        await execute_query(IDEMPOTENCY_SCHEMA_SQL)
        logger.info("Idempotency table created or verified")
        
    except Exception as e:
        logger.error(f"Failed to create idempotency table: {e}")
        raise