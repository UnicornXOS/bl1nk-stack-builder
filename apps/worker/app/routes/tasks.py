"""
Task management endpoints for bl1nk-agent-builder
Provides REST API for task creation, status, and streaming
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, status, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Pydantic models
class TaskCreateRequest(BaseModel):
    """Request model for creating a task"""
    task_type: str = Field(..., description="Type of task to create")
    input_data: Dict[str, Any] = Field(..., description="Input data for the task")
    priority: int = Field(default=2, description="Task priority (1-4)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TaskResponse(BaseModel):
    """Response model for task information"""
    task_id: int
    status: str
    task_type: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


router = APIRouter()

# Placeholder task storage (in production, this would be in database)
tasks_db = {}

@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(request: TaskCreateRequest, current_user: str = "demo_user"):
    """Create a new task"""
    
    task_id = len(tasks_db) + 1
    
    task_data = {
        "task_id": task_id,
        "status": "pending",
        "task_type": request.task_type,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "input_data": request.input_data,
        "priority": request.priority,
        "metadata": request.metadata,
        "user_id": current_user
    }
    
    tasks_db[task_id] = task_data
    
    logger.info(f"Task created: {task_id}")
    
    return TaskResponse(
        task_id=task_id,
        status="pending",
        task_type=request.task_type,
        created_at=task_data["created_at"]
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int):
    """Get task status and details"""
    
    if task_id not in tasks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    task_data = tasks_db[task_id]
    
    return TaskResponse(
        task_id=task_id,
        status=task_data["status"],
        task_type=task_data.get("task_type"),
        created_at=task_data["created_at"],
        updated_at=task_data["updated_at"],
        result=task_data.get("result"),
        error=task_data.get("error")
    )


@router.get("/tasks/{task_id}/stream")
async def stream_task_output(task_id: int):
    """Stream task output using Server-Sent Events"""
    
    if task_id not in tasks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    async def event_generator():
        task_data = tasks_db[task_id]
        
        # Send initial meta event
        yield f"data: {{\"type\": \"meta\", \"data\": {{\"task_id\": {task_id}, \"status\": \"{task_data['status']}\"}}}}\n\n"
        
        # Simulate streaming output
        if task_data["status"] == "pending":
            # Mark as processing
            task_data["status"] = "processing"
            yield f"data: {{\"type\": \"meta\", \"data\": {{\"status\": \"processing\"}}}}\n\n"
            
            # Send some text events
            messages = ["Hello", ", how can", " I help", " you today?"]
            for message in messages:
                yield f"data: {{\"type\": \"text\", \"data\": \"{message}\"}}\n\n"
                await asyncio.sleep(0.5)
            
            # Mark as completed
            task_data["status"] = "completed"
            task_data["result"] = {"response": "Hello, how can I help you today?"}
            yield f"data: {{\"type\": \"meta\", \"data\": {{\"status\": \"completed\"}}}}\n\n"
            yield f"data: {{\"type\": \"done\", \"data\": {{\"result\": {task_data['result']}}}}}\n\n"
        
        elif task_data["status"] == "completed":
            # Send completion event
            yield f"data: {{\"type\": \"meta\", \"data\": {{\"status\": \"completed\"}}}}\n\n"
            yield f"data: {{\"type\": \"done\", \"data\": {{\"result\": {task_data.get('result', '{}')}}}}}\n\n"
        
        elif task_data["status"] == "failed":
            # Send error event
            yield f"data: {{\"type\": \"meta\", \"data\": {{\"status\": \"failed\"}}}}\n\n"
            yield f"data: {{\"type\": \"error\", \"data\": {{\"error\": \"{task_data.get('error', 'Unknown error')}\"}}}}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """List tasks with optional filtering"""
    
    filtered_tasks = []
    
    for task_id, task_data in tasks_db.items():
        # Apply filters
        if status and task_data["status"] != status:
            continue
        if task_type and task_data.get("task_type") != task_type:
            continue
        
        filtered_tasks.append(task_data)
    
    # Apply pagination
    paginated_tasks = filtered_tasks[offset:offset + limit]
    
    return {
        "tasks": paginated_tasks,
        "total": len(filtered_tasks),
        "limit": limit,
        "offset": offset
    }


@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: int):
    """Cancel a task"""
    
    if task_id not in tasks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    task_data = tasks_db[task_id]
    
    if task_data["status"] in ["completed", "failed", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel task in {task_data['status']} state"
        )
    
    task_data["status"] = "cancelled"
    task_data["updated_at"] = datetime.now().isoformat()
    
    return {"message": f"Task {task_id} cancelled"}