"""
Task Orchestrator for bl1nk-agent-builder
Coordinates task execution across multiple providers and manages the task lifecycle
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from app.database.connection import fetch_one, execute_query, fetch_many
from app.database.redis import get_redis, set_task_status, get_task_status
from app.config.settings import settings
from app.utils.tracing import trace_operation, AsyncTraceContext
from app.utils.retry import retry_async, RetryConfig, RetryStrategy

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """Types of tasks"""
    CHAT = "chat"
    EMBEDDING = "embedding"
    RERANK = "rerank"
    SKILL_INVOCATION = "skill_invocation"
    MCP_TOOL_CALL = "mcp_tool_call"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class TaskOrchestrator:
    """Main task orchestrator for coordinating task execution"""
    
    def __init__(self, provider_manager, vector_store):
        self.provider_manager = provider_manager
        self.vector_store = vector_store
        self.redis = get_redis()
        self.active_tasks: Dict[int, Dict[str, Any]] = {}
        self.task_workers: Dict[str, asyncio.Task] = {}
        
    async def submit_task(
        self,
        task_type: TaskType,
        input_data: Dict[str, Any],
        user_id: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        metadata: Dict[str, Any] = None
    ) -> int:
        """Submit a new task for processing"""
        
        async with AsyncTraceContext("task_submit", task_type=task_type.value):
            
            try:
                # Create task record in database
                task_data = {
                    "user_id": user_id,
                    "task_type": task_type.value,
                    "input_data": input_data,
                    "priority": priority.value,
                    "status": TaskStatus.PENDING.value,
                    "metadata": metadata or {},
                    "created_at": datetime.now().isoformat()
                }
                
                task_id = await self._create_task_record(task_data)
                
                # Set initial task status in Redis
                await set_task_status(str(task_id), TaskStatus.PENDING.value, {
                    "task_id": task_id,
                    "task_type": task_type.value,
                    "user_id": user_id,
                    "priority": priority.value
                })
                
                # Add to queue based on priority
                await self._queue_task(task_id, priority)
                
                logger.info(
                    f"Task submitted successfully - ID: {task_id}, Type: {task_type.value}",
                    extra={
                        "event": "task_submitted",
                        "task_id": task_id,
                        "task_type": task_type.value,
                        "user_id": user_id,
                        "priority": priority.value
                    }
                )
                
                return task_id
                
            except Exception as e:
                logger.error(f"Failed to submit task: {e}", exc_info=True)
                raise
    
    async def get_task_status(self, task_id: int) -> Dict[str, Any]:
        """Get current status of a task"""
        
        try:
            # Try to get from Redis cache first
            redis_status = await get_task_status(str(task_id))
            if redis_status:
                return redis_status
            
            # Fallback to database
            task = await fetch_one(
                "SELECT * FROM tasks WHERE id = $1",
                task_id
            )
            
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            # Convert to status format
            status_data = {
                "task_id": task_id,
                "status": task["status"],
                "task_type": task.get("task_type"),
                "user_id": task["user_id"],
                "created_at": task["created_at"].isoformat() if task["created_at"] else None,
                "updated_at": task["updated_at"].isoformat() if task["updated_at"] else None,
                "result": task.get("output_payload"),
                "error": task.get("error_reason")
            }
            
            return status_data
            
        except Exception as e:
            logger.error(f"Failed to get task status for {task_id}: {e}")
            raise
    
    async def cancel_task(self, task_id: int) -> bool:
        """Cancel a pending or processing task"""
        
        try:
            # Update task status in database
            result = await execute_query(
                "UPDATE tasks SET status = $1, updated_at = NOW() WHERE id = $2 AND status IN ($3, $4)",
                TaskStatus.CANCELLED.value,
                task_id,
                TaskStatus.PENDING.value,
                TaskStatus.PROCESSING.value
            )
            
            if "0" in result:
                # Task was not found or not in cancelable state
                return False
            
            # Update Redis status
            await set_task_status(str(task_id), TaskStatus.CANCELLED.value, {
                "task_id": task_id,
                "cancelled_at": datetime.now().isoformat()
            })
            
            # Cancel worker if exists
            worker_task = self.task_workers.get(str(task_id))
            if worker_task and not worker_task.done():
                worker_task.cancel()
            
            logger.info(f"Task {task_id} cancelled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
    
    async def process_next_task(self) -> Optional[int]:
        """Process the next task from the queue"""
        
        try:
            # Get task from queue
            task_data = await self.redis.brpop(settings.task_queue_name, timeout=1)
            if not task_data:
                return None
            
            _, task_json = task_data
            import json
            task_info = json.loads(task_json)
            
            task_id = task_info["task_id"]
            
            # Start processing task
            await self._process_task(task_id, task_info)
            
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to process next task: {e}", exc_info=True)
            return None
    
    async def _process_task(self, task_id: int, task_info: Dict[str, Any]):
        """Process a specific task"""
        
        task_key = str(task_id)
        
        try:
            # Update task status to processing
            await execute_query(
                "UPDATE tasks SET status = $1, updated_at = NOW() WHERE id = $2",
                TaskStatus.PROCESSING.value,
                task_id
            )
            
            await set_task_status(task_key, TaskStatus.PROCESSING.value, {
                "task_id": task_id,
                "started_at": datetime.now().isoformat()
            })
            
            # Mark as active
            self.active_tasks[task_id] = task_info
            
            # Create worker task
            worker_task = asyncio.create_task(
                self._execute_task(task_id, task_info),
                name=f"task_worker_{task_id}"
            )
            
            self.task_workers[task_key] = worker_task
            
            # Wait for completion
            result = await worker_task
            
            if result["success"]:
                await self._complete_task(task_id, result["data"])
            else:
                await self._fail_task(task_id, result["error"])
                
        except asyncio.CancelledError:
            logger.info(f"Task {task_id} was cancelled")
            await self._fail_task(task_id, "Task was cancelled")
            
        except Exception as e:
            logger.error(f"Task {task_id} failed with error: {e}", exc_info=True)
            await self._fail_task(task_id, str(e))
            
        finally:
            # Clean up
            self.active_tasks.pop(task_id, None)
            self.task_workers.pop(task_key, None)
    
    async def _execute_task(self, task_id: int, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual task logic"""
        
        async with AsyncTraceContext("task_execution", task_id=task_id, task_type=task_info.get("type")):
            
            task_type = task_info.get("type")
            
            if task_type == "poe_chat":
                return await self._execute_chat_task(task_id, task_info)
            elif task_type == "embedding":
                return await self._execute_embedding_task(task_id, task_info)
            elif task_type == "rerank":
                return await self._execute_rerank_task(task_id, task_info)
            elif task_type == "skill_invocation":
                return await self._execute_skill_task(task_id, task_info)
            else:
                raise ValueError(f"Unknown task type: {task_type}")
    
    async def _execute_chat_task(self, task_id: int, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a chat task"""
        
        message = task_info.get("message")
        user_id = task_info.get("user_id")
        
        # Generate response using provider manager
        response = await self.provider_manager.generate_response(
            prompt=message,
            user_id=user_id,
            task_id=task_id
        )
        
        return {
            "success": True,
            "data": {
                "response": response,
                "model_used": response.get("model", "unknown"),
                "tokens_used": response.get("tokens", {}),
                "cost": response.get("cost", 0.0)
            }
        }
    
    async def _execute_embedding_task(self, task_id: int, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an embedding task"""
        
        text = task_info.get("text")
        model = task_info.get("model", "gamma-300")
        
        # Generate embedding
        embedding = await self.provider_manager.generate_embedding(
            text=text,
            model=model
        )
        
        # Store in vector store
        await self.vector_store.store_embedding(
            text=text,
            embedding=embedding,
            metadata=task_info.get("metadata", {})
        )
        
        return {
            "success": True,
            "data": {
                "embedding": embedding,
                "model_used": model,
                "dimension": len(embedding)
            }
        }
    
    async def _execute_rerank_task(self, task_id: int, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a rerank task"""
        
        query = task_info.get("query")
        documents = task_info.get("documents", [])
        
        # Rerank documents
        reranked = await self.provider_manager.rerank_documents(
            query=query,
            documents=documents
        )
        
        return {
            "success": True,
            "data": {
                "reranked_documents": reranked,
                "original_count": len(documents),
                "reranked_count": len(reranked)
            }
        }
    
    async def _execute_skill_task(self, task_id: int, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a skill invocation task"""
        
        skill_id = task_info.get("skill_id")
        inputs = task_info.get("inputs")
        
        # This would integrate with the skills system
        # For now, return a placeholder result
        
        return {
            "success": True,
            "data": {
                "skill_id": skill_id,
                "result": f"Skill {skill_id} executed with inputs: {inputs}",
                "execution_time": 1.0
            }
        }
    
    async def _complete_task(self, task_id: int, result_data: Dict[str, Any]):
        """Mark task as completed"""
        
        try:
            # Update database
            await execute_query(
                """
                UPDATE tasks 
                SET status = $1, output_payload = $2, updated_at = NOW() 
                WHERE id = $3
                """,
                TaskStatus.COMPLETED.value,
                result_data,
                task_id
            )
            
            # Update Redis
            await set_task_status(str(task_id), TaskStatus.COMPLETED.value, {
                "task_id": task_id,
                "completed_at": datetime.now().isoformat(),
                "result": result_data
            })
            
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to complete task {task_id}: {e}")
    
    async def _fail_task(self, task_id: int, error: str):
        """Mark task as failed"""
        
        try:
            # Update database
            await execute_query(
                """
                UPDATE tasks 
                SET status = $1, error_reason = $2, updated_at = NOW() 
                WHERE id = $3
                """,
                TaskStatus.FAILED.value,
                error,
                task_id
            )
            
            # Update Redis
            await set_task_status(str(task_id), TaskStatus.FAILED.value, {
                "task_id": task_id,
                "failed_at": datetime.now().isoformat(),
                "error": error
            })
            
            logger.error(f"Task {task_id} failed: {error}")
            
        except Exception as e:
            logger.error(f"Failed to mark task {task_id} as failed: {e}")
    
    async def _create_task_record(self, task_data: Dict[str, Any]) -> int:
        """Create task record in database"""
        
        import json
        
        result = await execute_query(
            """
            INSERT INTO tasks (
                user_id,
                task_type,
                input_payload,
                status,
                priority,
                metadata,
                created_at,
                updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
            RETURNING id
            """,
            task_data["user_id"],
            task_data["task_type"],
            json.dumps(task_data["input_data"]),
            task_data["status"],
            task_data["priority"],
            json.dumps(task_data["metadata"])
        )
        
        # Extract ID from result
        if isinstance(result, str) and " " in result:
            return int(result.split()[-1])
        elif isinstance(result, int):
            return result
        else:
            raise ValueError(f"Unexpected task ID format: {result}")
    
    async def _queue_task(self, task_id: int, priority: TaskPriority):
        """Add task to appropriate queue based on priority"""
        
        # For now, use a single queue with priority
        # In production, you might use separate queues for different priorities
        await self.redis.lpush(settings.task_queue_name, str(task_id))
    
    async def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get list of currently active tasks"""
        
        active = []
        for task_id, task_info in self.active_tasks.items():
            status_info = await self.get_task_status(task_id)
            active.append({
                "task_id": task_id,
                "task_info": task_info,
                "status_info": status_info
            })
        
        return active
    
    async def cleanup_completed_tasks(self):
        """Clean up old completed tasks from active tracking"""
        
        completed_task_ids = []
        
        for task_id in list(self.active_tasks.keys()):
            status_info = await self.get_task_status(task_id)
            if status_info.get("status") in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value]:
                completed_task_ids.append(task_id)
        
        for task_id in completed_task_ids:
            self.active_tasks.pop(task_id, None)
            self.task_workers.pop(str(task_id), None)
        
        if completed_task_ids:
            logger.info(f"Cleaned up {len(completed_task_ids)} completed tasks")
    
    async def shutdown(self):
        """Shutdown the task orchestrator"""
        
        logger.info("Shutting down task orchestrator...")
        
        # Cancel all active workers
        for task_key, worker_task in self.task_workers.items():
            if not worker_task.done():
                worker_task.cancel()
        
        # Wait for workers to complete
        if self.task_workers:
            await asyncio.gather(*self.task_workers.values(), return_exceptions=True)
        
        logger.info("Task orchestrator shutdown complete")