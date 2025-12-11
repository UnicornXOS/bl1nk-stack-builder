"""
Server-Sent Events utilities for bl1nk-agent-builder
Provides SSE streaming functionality for real-time updates
"""

import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, Optional, Callable
from datetime import datetime

from fastapi import Request, Response
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)


class SSEManager:
    """Manager for Server-Sent Events connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        self.connection_count = 0
    
    async def add_connection(
        self, 
        connection_id: str, 
        task_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> None:
        """Add a new SSE connection"""
        
        self.active_connections[connection_id] = {
            "task_id": task_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        
        self.connection_count += 1
        
        logger.info(
            f"SSE connection added: {connection_id}",
            extra={
                "event": "sse_connection_added",
                "connection_id": connection_id,
                "task_id": task_id,
                "user_id": user_id,
                "total_connections": self.connection_count
            }
        )
    
    async def remove_connection(self, connection_id: str) -> None:
        """Remove an SSE connection"""
        
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            self.connection_count -= 1
            
            logger.info(
                f"SSE connection removed: {connection_id}",
                extra={
                    "event": "sse_connection_removed",
                    "connection_id": connection_id,
                    "total_connections": self.connection_count
                }
            )
    
    async def send_to_connection(
        self, 
        connection_id: str, 
        data: Dict[str, Any]
    ) -> bool:
        """Send data to a specific connection"""
        
        if connection_id not in self.active_connections:
            return False
        
        # Update last activity
        self.active_connections[connection_id]["last_activity"] = datetime.now().isoformat()
        
        # Format SSE event
        event_data = {
            "timestamp": datetime.now().isoformat(),
            "connection_id": connection_id,
            **data
        }
        
        # In a real implementation, this would send to the actual connection
        # For now, we just log it
        logger.debug(
            f"SSE event sent to {connection_id}",
            extra={
                "event": "sse_event_sent",
                "connection_id": connection_id,
                "event_type": data.get("type"),
                "data": event_data
            }
        )
        
        return True
    
    async def broadcast_to_task(self, task_id: str, data: Dict[str, Any]) -> int:
        """Broadcast data to all connections for a specific task"""
        
        sent_count = 0
        
        for connection_id, connection_info in self.active_connections.items():
            if connection_info.get("task_id") == task_id:
                if await self.send_to_connection(connection_id, data):
                    sent_count += 1
        
        logger.debug(
            f"SSE broadcast to task {task_id}: {sent_count} connections",
            extra={
                "event": "sse_broadcast_task",
                "task_id": task_id,
                "connections_reached": sent_count,
                "event_type": data.get("type")
            }
        )
        
        return sent_count
    
    async def broadcast_to_user(self, user_id: str, data: Dict[str, Any]) -> int:
        """Broadcast data to all connections for a specific user"""
        
        sent_count = 0
        
        for connection_id, connection_info in self.active_connections.items():
            if connection_info.get("user_id") == user_id:
                if await self.send_to_connection(connection_id, data):
                    sent_count += 1
        
        logger.debug(
            f"SSE broadcast to user {user_id}: {sent_count} connections",
            extra={
                "event": "sse_broadcast_user",
                "user_id": user_id,
                "connections_reached": sent_count,
                "event_type": data.get("type")
            }
        )
        
        return sent_count
    
    async def cleanup_stale_connections(self, max_age_hours: int = 24) -> int:
        """Clean up stale connections"""
        
        stale_connections = []
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        for connection_id, connection_info in self.active_connections.items():
            last_activity = datetime.fromisoformat(connection_info["last_activity"])
            if last_activity < cutoff_time:
                stale_connections.append(connection_id)
        
        # Remove stale connections
        for connection_id in stale_connections:
            await self.remove_connection(connection_id)
        
        if stale_connections:
            logger.info(
                f"Cleaned up {len(stale_connections)} stale SSE connections",
                extra={
                    "event": "sse_cleanup",
                    "connections_removed": len(stale_connections),
                    "max_age_hours": max_age_hours
                }
            )
        
        return len(stale_connections)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about SSE connections"""
        
        return {
            "total_connections": self.connection_count,
            "active_connections": len(self.active_connections),
            "connections": list(self.active_connections.keys())
        }


# Global SSE manager instance
sse_manager = SSEManager()


class SSEEvent:
    """Represents an SSE event"""
    
    def __init__(
        self, 
        event_type: str, 
        data: Dict[str, Any], 
        event_id: Optional[str] = None
    ):
        self.event_type = event_type
        self.data = data
        self.event_id = event_id or f"evt_{int(datetime.now().timestamp() * 1000)}"
        self.timestamp = datetime.now()
    
    def to_sse_format(self) -> str:
        """Convert event to SSE format string"""
        
        lines = []
        
        # Add event ID
        lines.append(f"id: {self.event_id}")
        
        # Add event type
        lines.append(f"event: {self.event_type}")
        
        # Add data
        data_json = json.dumps(self.data, default=str)
        lines.append(f"data: {data_json}")
        
        # Add blank line to separate events
        lines.append("")
        
        return "\n".join(lines)


async def create_sse_response(
    request: Request,
    event_generator: AsyncGenerator[str, None],
    connection_id: str
) -> StreamingResponse:
    """Create an SSE response with proper headers"""
    
    async def sse_generator():
        """Generator that yields SSE events"""
        try:
            async for event_data in event_generator:
                if isinstance(event_data, dict):
                    # Convert dict to SSE format
                    event = SSEEvent(
                        event_type=event_data.get("type", "message"),
                        data=event_data
                    )
                    yield event.to_sse_format()
                else:
                    # Assume it's already in SSE format
                    yield event_data
        except asyncio.CancelledError:
            logger.info(
                f"SSE connection cancelled: {connection_id}",
                extra={
                    "event": "sse_connection_cancelled",
                    "connection_id": connection_id
                }
            )
        except Exception as e:
            logger.error(
                f"SSE connection error: {connection_id} - {e}",
                extra={
                    "event": "sse_connection_error",
                    "connection_id": connection_id,
                    "error": str(e)
                },
                exc_info=True
            )
        finally:
            # Clean up connection
            await sse_manager.remove_connection(connection_id)
    
    # Add connection to manager
    await sse_manager.add_connection(connection_id)
    
    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
            "Access-Control-Allow-Headers": "X-Requested-With"
        }
    )


async def stream_task_events(task_id: str) -> AsyncGenerator[Dict[str, Any], None]:
    """Stream events for a specific task"""
    
    # This would typically poll the task status from database/queue
    # For now, we'll simulate some events
    
    # Meta event
    yield {
        "type": "meta",
        "data": {
            "task_id": task_id,
            "status": "started",
            "message": "Task processing started"
        }
    }
    
    # Simulate some processing events
    for i in range(5):
        await asyncio.sleep(1)  # Simulate processing time
        
        yield {
            "type": "progress",
            "data": {
                "task_id": task_id,
                "progress": (i + 1) * 20,
                "message": f"Processing step {i + 1}"
            }
        }
    
    # Final result
    yield {
        "type": "done",
        "data": {
            "task_id": task_id,
            "status": "completed",
            "result": {
                "output": "Task completed successfully",
                "processing_time": 5.2
            }
        }
    }


async def stream_heartbeat() -> AsyncGenerator[Dict[str, Any], None]:
    """Stream heartbeat events to keep connection alive"""
    
    while True:
        yield {
            "type": "heartbeat",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "message": "Connection alive"
            }
        }
        
        await asyncio.sleep(30)  # Send heartbeat every 30 seconds


# Event generators for different scenarios
async def stream_error_events(error_message: str) -> AsyncGenerator[Dict[str, Any], None]:
    """Stream error events"""
    
    yield {
        "type": "error",
        "data": {
            "error": error_message,
            "timestamp": datetime.now().isoformat()
        }
    }


async def stream_chat_events(messages: list) -> AsyncGenerator[Dict[str, Any], None]:
    """Stream chat message events"""
    
    for message in messages:
        yield {
            "type": "text",
            "data": {
                "content": message,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        await asyncio.sleep(0.5)  # Simulate streaming delay


# Utility functions
def format_sse_event(event_type: str, data: Dict[str, Any]) -> str:
    """Format a single SSE event"""
    
    event = SSEEvent(event_type, data)
    return event.to_sse_format()


async def send_sse_event(
    connection_id: str, 
    event_type: str, 
    data: Dict[str, Any]
) -> bool:
    """Send an SSE event to a specific connection"""
    
    return await sse_manager.send_to_connection(
        connection_id, 
        {"type": event_type, "data": data}
    )


async def broadcast_sse_event(
    event_type: str, 
    data: Dict[str, Any], 
    task_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> int:
    """Broadcast an SSE event"""
    
    if task_id:
        return await sse_manager.broadcast_to_task(task_id, {"type": event_type, "data": data})
    elif user_id:
        return await sse_manager.broadcast_to_user(user_id, {"type": event_type, "data": data})
    else:
        # Broadcast to all connections
        sent_count = 0
        for connection_id in list(sse_manager.active_connections.keys()):
            if await sse_manager.send_to_connection(connection_id, {"type": event_type, "data": data}):
                sent_count += 1
        return sent_count


# Cleanup task
async def cleanup_sse_connections():
    """Periodic cleanup of stale SSE connections"""
    
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            cleaned = await sse_manager.cleanup_stale_connections()
            
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} stale SSE connections")
                
        except Exception as e:
            logger.error(f"Error during SSE cleanup: {e}")


from datetime import timedelta