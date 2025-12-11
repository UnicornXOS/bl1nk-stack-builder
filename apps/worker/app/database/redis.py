"""
Redis connection and management for bl1nk-agent-builder
Handles Upstash Redis for queue management and caching
"""

import asyncio
import logging
from typing import Optional, Any, Dict, List
from contextlib import asynccontextmanager

import aioredis
from aioredis import Redis

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Global Redis connection
_redis_client: Optional[Redis] = None


async def init_redis() -> None:
    """Initialize Redis connection"""
    global _redis_client
    
    logger.info("Initializing Redis connection...")
    
    try:
        # Parse Redis URL
        if settings.redis_url.startswith('rediss://'):
            # SSL connection for Upstash
            _redis_client = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                ssl=True
            )
        else:
            # Standard connection
            _redis_client = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        
        # Test connection
        await _redis_client.ping()
        
        logger.info("Redis connection initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Redis connection: {e}")
        raise


async def close_redis() -> None:
    """Close Redis connection"""
    global _redis_client
    
    if _redis_client:
        logger.info("Closing Redis connection...")
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")


def get_redis() -> Redis:
    """Get Redis client instance"""
    if not _redis_client:
        raise RuntimeError("Redis connection not initialized")
    return _redis_client


# Queue Management
async def enqueue_task(task_data: Dict[str, Any], priority: int = 0) -> str:
    """Add task to queue"""
    redis = get_redis()
    
    # Use sorted set for priority queue
    queue_name = settings.task_queue_name
    score = -priority  # Negative for descending order
    
    task_json = str(task_data)
    task_id = await redis.lpush(queue_name, task_json)
    
    logger.debug(f"Enqueued task {task_id} with priority {priority}")
    return str(task_id)


async def dequeue_task(timeout: int = 30) -> Optional[Dict[str, Any]]:
    """Get task from queue"""
    redis = get_redis()
    
    queue_name = settings.task_queue_name
    
    # Use BRPOP for blocking pop with timeout
    result = await redis.brpop(queue_name, timeout=timeout)
    
    if result:
        _, task_data = result
        logger.debug(f"Dequeued task: {task_data}")
        return eval(task_data)  # Convert string back to dict
    
    return None


async def get_queue_length() -> int:
    """Get current queue length"""
    redis = get_redis()
    return await redis.llen(settings.task_queue_name)


# Rate Limiting
async def check_rate_limit(user_id: str, provider: str, limit: int, window: int = 60) -> bool:
    """Check if user is within rate limit"""
    redis = get_redis()
    
    key = f"ratelimit:{user_id}:{provider}"
    
    # Use INCR with EX for sliding window
    current = await redis.incr(key)
    
    if current == 1:
        # First request in this window, set expiration
        await redis.expire(key, window)
    
    return current <= limit


async def increment_usage(user_id: str, provider: str, amount: int = 1) -> int:
    """Increment usage counter for user/provider"""
    redis = get_redis()
    
    key = f"usage:{user_id}:{provider}:{settings.environment}"
    current = await redis.incrby(key, amount)
    
    # Set daily expiration
    await redis.expire(key, 86400)  # 24 hours
    
    return current


# Caching
async def cache_get(key: str) -> Optional[str]:
    """Get value from cache"""
    redis = get_redis()
    return await redis.get(key)


async def cache_set(key: str, value: str, ttl: int = None) -> bool:
    """Set value in cache with optional TTL"""
    redis = get_redis()
    
    if ttl:
        return await redis.setex(key, ttl, value)
    else:
        return await redis.set(key, value)


async def cache_delete(key: str) -> bool:
    """Delete value from cache"""
    redis = get_redis()
    return await redis.delete(key) > 0


# Embedding Cache
async def get_embedding_cache(text_hash: str, model: str) -> Optional[List[float]]:
    """Get cached embedding"""
    redis = get_redis()
    
    key = f"embedding:{model}:{text_hash}"
    cached = await redis.get(key)
    
    if cached:
        import json
        return json.loads(cached)
    
    return None


async def set_embedding_cache(text_hash: str, model: str, embedding: List[float], ttl: int = None) -> bool:
    """Cache embedding with TTL"""
    redis = get_redis()
    
    key = f"embedding:{model}:{text_hash}"
    import json
    
    embedding_json = json.dumps(embedding)
    
    if ttl:
        return await redis.setex(key, ttl, embedding_json)
    else:
        return await redis.set(key, embedding_json)


# Token Bucket (for rate limiting)
async def consume_tokens(bucket_name: str, tokens: int = 1, capacity: int = 100, refill_rate: float = 1.0) -> bool:
    """Consume tokens from bucket (token bucket algorithm)"""
    redis = get_redis()
    
    key = f"bucket:{bucket_name}"
    
    # Lua script for atomic token bucket operation
    lua_script = """
    local bucket_key = KEYS[1]
    local tokens = tonumber(ARGV[1])
    local capacity = tonumber(ARGV[2])
    local refill_rate = tonumber(ARGV[3])
    local current_time = tonumber(ARGV[4])
    
    local tokens_in_bucket = redis.call('GET', bucket_key)
    local last_refill = redis.call('GET', bucket_key .. ':last_refill')
    
    if not tokens_in_bucket then
        tokens_in_bucket = capacity
        last_refill = current_time
    else
        tokens_in_bucket = tonumber(tokens_in_bucket)
        last_refill = tonumber(last_refill) or current_time
    end
    
    -- Calculate tokens to add based on time passed
    local time_passed = current_time - last_refill
    local tokens_to_add = time_passed * refill_rate
    tokens_in_bucket = math.min(capacity, tokens_in_bucket + tokens_to_add)
    
    -- Check if enough tokens and consume
    if tokens_in_bucket >= tokens then
        tokens_in_bucket = tokens_in_bucket - tokens
        redis.call('SET', bucket_key, tokens_in_bucket)
        redis.call('SET', bucket_key .. ':last_refill', current_time)
        return 1
    else
        return 0
    end
    """
    
    current_time = asyncio.get_event_loop().time()
    
    result = await redis.eval(
        lua_script,
        1,
        key,
        str(tokens),
        str(capacity),
        str(refill_rate),
        str(current_time)
    )
    
    return bool(result)


# Task Status Tracking
async def set_task_status(task_id: str, status: str, data: Dict[str, Any] = None) -> bool:
    """Set task status with optional data"""
    redis = get_redis()
    
    key = f"task:{task_id}:status"
    status_data = {
        "status": status,
        "updated_at": asyncio.get_event_loop().time(),
        "data": data or {}
    }
    
    import json
    return await redis.setex(key, 86400, json.dumps(status_data))  # 24h TTL


async def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """Get task status"""
    redis = get_redis()
    
    key = f"task:{task_id}:status"
    status_data = await redis.get(key)
    
    if status_data:
        import json
        return json.loads(status_data)
    
    return None


# Health Check
async def redis_health_check() -> Dict[str, Any]:
    """Check Redis health"""
    try:
        redis = get_redis()
        
        # Basic ping
        pong = await redis.ping()
        
        # Get Redis info
        info = await redis.info()
        
        return {
            "status": "healthy",
            "ping": pong,
            "memory_used": info.get('used_memory_human'),
            "connected_clients": info.get('connected_clients'),
            "queue_length": await get_queue_length()
        }
        
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }