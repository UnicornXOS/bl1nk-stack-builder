"""
Tracing utilities for bl1nk-agent-builder
Handles request tracing, correlation IDs, and distributed tracing
"""

import logging
import uuid
import time
from typing import Optional, Dict, Any
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TraceContext:
    """Trace context data structure"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    baggage: Dict[str, Any]
    start_time: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "baggage": self.baggage,
            "start_time": self.start_time
        }


class TraceManager:
    """Manager for trace context and operations"""
    
    def __init__(self):
        self.current_context: Optional[TraceContext] = None
    
    def generate_trace_id(self) -> str:
        """Generate a new trace ID"""
        return str(uuid.uuid4()).replace("-", "")[:32]
    
    def generate_span_id(self) -> str:
        """Generate a new span ID"""
        return str(uuid.uuid4()).replace("-", "")[:16]
    
    def create_trace_context(
        self, 
        parent_context: Optional['TraceContext'] = None,
        baggage: Dict[str, Any] = None
    ) -> TraceContext:
        """Create a new trace context"""
        
        if parent_context:
            # Child span
            trace_id = parent_context.trace_id
            parent_span_id = parent_context.span_id
        else:
            # Root span
            trace_id = self.generate_trace_id()
            parent_span_id = None
        
        span_id = self.generate_span_id()
        
        context = TraceContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            baggage=baggage or {},
            start_time=time.time()
        )
        
        self.current_context = context
        return context
    
    def get_current_context(self) -> Optional[TraceContext]:
        """Get current trace context"""
        return self.current_context
    
    def set_baggage_item(self, key: str, value: Any) -> None:
        """Set baggage item in current context"""
        if self.current_context:
            self.current_context.baggage[key] = value
    
    def get_baggage_item(self, key: str) -> Optional[Any]:
        """Get baggage item from current context"""
        if self.current_context:
            return self.current_context.baggage.get(key)
        return None


# Global trace manager instance
trace_manager = TraceManager()


def get_trace_id(request_or_context=None) -> str:
    """Get trace ID from request or current context"""
    
    # Try to get from request
    if hasattr(request_or_context, 'state') and hasattr(request_or_context.state, 'trace_id'):
        return request_or_context.state.trace_id
    
    # Try to get from current context
    context = trace_manager.get_current_context()
    if context:
        return context.trace_id
    
    # Generate new trace ID
    return trace_manager.generate_trace_id()


def create_child_span(parent_context: Optional[TraceContext] = None, **kwargs) -> TraceContext:
    """Create a child span from parent context"""
    
    if not parent_context:
        parent_context = trace_manager.get_current_context()
    
    return trace_manager.create_trace_context(
        parent_context=parent_context,
        baggage=kwargs
    )


def create_root_span(**kwargs) -> TraceContext:
    """Create a new root span"""
    
    return trace_manager.create_trace_context(
        parent_context=None,
        baggage=kwargs
    )


@contextmanager
def trace_operation(operation_name: str, **tags):
    """Context manager for tracing operations"""
    
    # Create new span
    span = create_root_span(**tags) if not trace_manager.get_current_context() else create_child_span()
    span.operation_name = operation_name
    
    start_time = time.time()
    
    try:
        logger.debug(
            f"Starting trace operation: {operation_name}",
            extra={
                "event": "trace_operation_start",
                "operation_name": operation_name,
                "trace_id": span.trace_id,
                "span_id": span.span_id,
                "tags": tags
            }
        )
        
        yield span
        
    except Exception as e:
        # Log error with trace context
        duration = time.time() - start_time
        
        logger.error(
            f"Trace operation failed: {operation_name} - {str(e)}",
            extra={
                "event": "trace_operation_error",
                "operation_name": operation_name,
                "trace_id": span.trace_id,
                "span_id": span.span_id,
                "duration": duration,
                "error": str(e),
                "tags": tags
            },
            exc_info=True
        )
        
        raise
        
    finally:
        # Log completion
        duration = time.time() - start_time
        
        logger.info(
            f"Trace operation completed: {operation_name} ({duration:.3f}s)",
            extra={
                "event": "trace_operation_complete",
                "operation_name": operation_name,
                "trace_id": span.trace_id,
                "span_id": span.span_id,
                "duration": duration,
                "tags": tags
            }
        )


def log_with_trace(
    logger_instance: logging.Logger,
    level: int,
    message: str,
    request_or_context=None,
    **extra
) -> None:
    """Log message with trace correlation"""
    
    trace_id = get_trace_id(request_or_context)
    
    # Add trace context to extra
    trace_extra = {
        "trace_id": trace_id,
        **extra
    }
    
    logger_instance.log(level, message, extra=trace_extra)


def get_trace_headers(trace_context: Optional[TraceContext] = None) -> Dict[str, str]:
    """Get trace headers for propagation"""
    
    if not trace_context:
        trace_context = trace_manager.get_current_context()
    
    if not trace_context:
        return {}
    
    headers = {
        "X-Trace-Id": trace_context.trace_id,
        "X-Span-Id": trace_context.span_id,
    }
    
    if trace_context.parent_span_id:
        headers["X-Parent-Span-Id"] = trace_context.parent_span_id
    
    # Add OpenTelemetry traceparent header
    traceparent = f"00-{trace_context.trace_id}-{trace_context.span_id}-01"
    headers["traceparent"] = traceparent
    
    return headers


def parse_trace_headers(headers: Dict[str, str]) -> Optional[TraceContext]:
    """Parse trace headers and create context"""
    
    # Try to extract from traceparent (OpenTelemetry format)
    traceparent = headers.get("traceparent")
    if traceparent and traceparent.startswith("00-"):
        parts = traceparent.split("-")
        if len(parts) >= 3:
            trace_id = parts[1]
            span_id = parts[2]
            parent_span_id = None
            
            return TraceContext(
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                baggage={},
                start_time=time.time()
            )
    
    # Fallback to custom headers
    trace_id = headers.get("X-Trace-Id")
    span_id = headers.get("X-Span-Id")
    parent_span_id = headers.get("X-Parent-Span-Id")
    
    if trace_id and span_id:
        return TraceContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            baggage={},
            start_time=time.time()
        )
    
    return None


# Async context manager for trace correlation
class AsyncTraceContext:
    """Async context manager for trace operations"""
    
    def __init__(self, operation_name: str, **tags):
        self.operation_name = operation_name
        self.tags = tags
        self.span = None
        self.start_time = None
    
    async def __aenter__(self):
        self.span = create_root_span(**self.tags) if not trace_manager.get_current_context() else create_child_span()
        self.span.operation_name = self.operation_name
        self.start_time = time.time()
        
        logger.debug(
            f"Starting async trace operation: {self.operation_name}",
            extra={
                "event": "async_trace_operation_start",
                "operation_name": self.operation_name,
                "trace_id": self.span.trace_id,
                "span_id": self.span.span_id,
                "tags": self.tags
            }
        )
        
        return self.span
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type:
            logger.error(
                f"Async trace operation failed: {self.operation_name} - {str(exc_val)}",
                extra={
                    "event": "async_trace_operation_error",
                    "operation_name": self.operation_name,
                    "trace_id": self.span.trace_id,
                    "span_id": self.span.span_id,
                    "duration": duration,
                    "error": str(exc_val),
                    "tags": self.tags
                },
                exc_info=True
            )
        else:
            logger.info(
                f"Async trace operation completed: {self.operation_name} ({duration:.3f}s)",
                extra={
                    "event": "async_trace_operation_complete",
                    "operation_name": self.operation_name,
                    "trace_id": self.span.trace_id,
                    "span_id": self.span.span_id,
                    "duration": duration,
                    "tags": self.tags
                }
            )


# Decorator for automatic tracing
def trace_function(operation_name: str = None, **tags):
    """Decorator for automatic function tracing"""
    
    def decorator(func):
        operation = operation_name or f"{func.__module__}.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            async with AsyncTraceContext(operation, **tags):
                return await func(*args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            with trace_operation(operation, **tags):
                return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Utility functions for common tracing patterns
async def trace_database_operation(operation: str, query: str, params: tuple = None):
    """Trace database operations"""
    
    async with AsyncTraceContext(f"db_{operation}", query=query, params=str(params)):
        # Database operation will be executed by the caller
        pass


async def trace_provider_call(provider: str, model: str, operation: str = "generate"):
    """Trace provider API calls"""
    
    async with AsyncTraceContext(f"provider_{provider}", provider=provider, model=model, operation=operation):
        # Provider call will be executed by the caller
        pass


async def trace_task_processing(task_id: int, task_type: str):
    """Trace task processing"""
    
    async with AsyncTraceContext(f"task_processing", task_id=task_id, task_type=task_type):
        # Task processing will be executed by the caller
        pass


# Initialize tracing system
def init_tracing():
    """Initialize tracing system"""
    
    logger.info("Initializing tracing system")
    
    # Create root span for application startup
    root_span = create_root_span(
        event="application_startup",
        service="bl1nk-agent-builder",
        version="1.0.0"
    )
    
    logger.info(
        "Tracing system initialized",
        extra={
            "event": "tracing_initialized",
            "trace_id": root_span.trace_id,
            "span_id": root_span.span_id
        }
    )


import asyncio