"""
Tracing middleware for bl1nk-agent-builder
Handles request tracing, correlation IDs, and OpenTelemetry integration
"""

import asyncio
import logging
import uuid
import time
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.settings import settings

logger = logging.getLogger(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware for request tracing and correlation"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate or extract trace ID
        trace_id = self._get_or_create_trace_id(request)
        request.state.trace_id = trace_id
        
        # Set correlation ID for logging
        self._setup_logging_context(trace_id)
        
        # Start timing
        start_time = time.time()
        
        try:
            # Add trace headers to request for propagation
            request.state.start_time = start_time
            request.state.original_trace_id = trace_id
            
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Add trace headers to response
            self._add_trace_headers(response, trace_id, duration)
            
            # Log request completion
            self._log_request_completion(request, response, duration, trace_id)
            
            return response
            
        except Exception as e:
            # Calculate duration for failed requests
            duration = time.time() - start_time
            
            # Log error with trace context
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra={
                    "event": "request_error",
                    "trace_id": trace_id,
                    "method": request.method,
                    "url": str(request.url),
                    "duration": duration,
                    "error": str(e),
                },
                exc_info=True
            )
            
            raise
    
    def _get_or_create_trace_id(self, request: Request) -> str:
        """Get existing trace ID or create new one"""
        # Try to get trace ID from headers (standard OpenTelemetry headers)
        trace_id = (
            request.headers.get("traceparent") or
            request.headers.get("X-Trace-Id") or
            request.headers.get("X-Correlation-Id") or
            request.headers.get("X-Request-Id")
        )
        
        # If we got a traceparent header, extract trace ID
        if trace_id and trace_id.startswith("00-"):
            # Format: 00-trace_id-span_id-trace_flags
            parts = trace_id.split("-")
            if len(parts) >= 2:
                return parts[1]
        
        # If we got a simple trace ID, use it
        if trace_id and len(trace_id) == 32:  # Standard trace ID length
            return trace_id
        
        # Generate new trace ID
        return str(uuid.uuid4()).replace("-", "")[:32]
    
    def _setup_logging_context(self, trace_id: str) -> None:
        """Setup logging context for trace correlation"""
        # Add trace ID to all subsequent log messages
        logging.setLogRecordFactory(
            lambda name, level, pathname, lineno, msg, args, exc_info, **kwargs: logging.LogRecord(
                name, level, pathname, lineno, msg, args, exc_info,
                **kwargs, extra={"trace_id": trace_id}
            )
        )
    
    def _add_trace_headers(self, response: Response, trace_id: str, duration: float) -> None:
        """Add trace headers to response"""
        # Add our custom trace headers
        response.headers["X-Trace-Id"] = trace_id
        response.headers["X-Request-Id"] = trace_id
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        
        # Add OpenTelemetry traceparent header
        traceparent = f"00-{trace_id}-0000000000000000-01"
        response.headers["traceparent"] = traceparent
        
        # Add timing headers for client monitoring
        response.headers["X-Timing-Duration"] = str(int(duration * 1000))  # milliseconds
    
    def _log_request_completion(self, request: Request, response: Response, duration: float, trace_id: str) -> None:
        """Log request completion with trace context"""
        
        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO
        
        # Extract additional context
        user_agent = request.headers.get("User-Agent", "")
        content_length = response.headers.get("Content-Length", "0")
        
        # Log the request
        logger.log(
            log_level,
            f"{request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)",
            extra={
                "event": "request_completion",
                "trace_id": trace_id,
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "duration": duration,
                "user_agent": user_agent,
                "content_length": content_length,
                "request_id": trace_id,
            }
        )


class TraceContextMiddleware(BaseHTTPMiddleware):
    """Middleware to propagate trace context to background tasks"""
    
    async def dispatch(self, request: Request, call_next):
        # Store trace context
        trace_id = getattr(request.state, 'trace_id', None)
        
        if trace_id:
            # Store trace context in asyncio task for later retrieval
            task = asyncio.current_task()
            if task:
                task.set_name(f"trace:{trace_id}")
        
        return await call_next(request)


def setup_tracing(app: FastAPI) -> None:
    """Setup tracing middleware for the application"""
    
    # Add tracing middleware
    app.add_middleware(TracingMiddleware)
    
    # Add trace context middleware
    app.add_middleware(TraceContextMiddleware)
    
    logger.info("Tracing middleware configured")


def get_trace_id(request: Request) -> str:
    """Get trace ID from request"""
    return getattr(request.state, 'trace_id', 'unknown')


def create_child_trace(parent_trace_id: str) -> str:
    """Create a child trace ID"""
    return str(uuid.uuid4()).replace("-", "")[:32]


# Context manager for manual trace correlation
class TraceContext:
    """Context manager for trace correlation in background tasks"""
    
    def __init__(self, trace_id: str):
        self.trace_id = trace_id
        self.previous_factory = None
    
    def __enter__(self):
        # Store current factory
        self.previous_factory = logging.getLogRecordFactory()
        
        # Create new factory with trace context
        def trace_log_factory(name, level, pathname, lineno, msg, args, exc_info, **kwargs):
            return logging.LogRecord(
                name, level, pathname, lineno, msg, args, exc_info,
                **kwargs, extra={"trace_id": self.trace_id}
            )
        
        logging.setLogRecordFactory(trace_log_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous factory
        if self.previous_factory:
            logging.setLogRecordFactory(self.previous_factory)


# Utility functions for trace correlation
def correlate_logs(trace_id: str, **extra):
    """Create extra context for logging with trace correlation"""
    return {"trace_id": trace_id, **extra}


def log_with_trace(logger_instance: logging.Logger, level: int, message: str, trace_id: str, **extra):
    """Log message with trace correlation"""
    logger_instance.log(
        level,
        message,
        extra=correlate_logs(trace_id, **extra)
    )


# OpenTelemetry integration helpers (for future expansion)
def setup_opentelemetry():
    """Setup OpenTelemetry integration (when needed)"""
    if not settings.otel_exporter_otlp_endpoint:
        logger.info("OpenTelemetry endpoint not configured, skipping setup")
        return
    
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        
        # Setup tracer provider
        trace.set_tracer_provider(TracerProvider())
        tracer = trace.get_tracer(__name__)
        
        # Setup OTLP exporter
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.otel_exporter_otlp_endpoint
        )
        
        # Add span processor
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        
        logger.info("OpenTelemetry tracing configured")
        
    except ImportError:
        logger.warning("OpenTelemetry not installed, skipping OTLP setup")
    except Exception as e:
        logger.error(f"Failed to setup OpenTelemetry: {e}")


# Async context manager for trace correlation in background tasks
class TraceContextManager:
    """Async context manager for trace correlation"""
    
    def __init__(self, trace_id: str):
        self.trace_id = trace_id
        self.task = None
    
    async def __aenter__(self):
        # Store current task
        self.task = asyncio.current_task()
        if self.task:
            self.task.set_name(f"trace:{self.trace_id}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Clean up if needed
        pass