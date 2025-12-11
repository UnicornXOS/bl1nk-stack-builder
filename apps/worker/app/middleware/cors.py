"""
CORS middleware for bl1nk-agent-builder
Handles Cross-Origin Resource Sharing configuration
"""

import asyncio
import logging
from typing import List, Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.settings import settings

logger = logging.getLogger(__name__)


def setup_cors(app: FastAPI) -> None:
    """Setup CORS middleware for the application"""
    
    # Get allowed origins from environment
    allowed_origins = [
        "https://bl1nk.site",
        "https://www.bl1nk.site",
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:5173",  # Vite dev server
        "http://localhost:4173",  # Alternative dev port
    ]
    
    # Add environment-specific origins
    if settings.is_development:
        allowed_origins.extend([
            "http://localhost:8000",  # FastAPI dev server
            "http://127.0.0.1:8000",
            "http://localhost:3001",
        ])
    
    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-Trace-Id",
            "X-Request-Id",
            "X-Admin-Key",
            "Accept",
            "Accept-Language",
            "Content-Length",
            "Cache-Control",
        ],
        expose_headers=[
            "X-Trace-Id",
            "X-Request-Id",
            "X-Admin-Key",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ],
        max_age=86400,  # 24 hours
    )
    
    logger.info(f"CORS configured with origins: {allowed_origins}")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HSTS (only for HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' https://api.bl1nk.site; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for debugging and monitoring"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = asyncio.get_event_loop().time()
        
        # Extract request info
        method = request.method
        url = str(request.url)
        user_agent = request.headers.get("User-Agent", "")
        trace_id = request.headers.get("X-Trace-Id", "unknown")
        
        # Log request start
        logger.info(
            f"Request started: {method} {url}",
            extra={
                "event": "request_start",
                "method": method,
                "url": url,
                "trace_id": trace_id,
                "user_agent": user_agent,
            }
        )
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = asyncio.get_event_loop().time() - start_time
            
            # Log request completion
            logger.info(
                f"Request completed: {method} {url} - {response.status_code} ({duration:.3f}s)",
                extra={
                    "event": "request_complete",
                    "method": method,
                    "url": url,
                    "status_code": response.status_code,
                    "duration": duration,
                    "trace_id": trace_id,
                }
            )
            
            # Add response headers
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            response.headers["X-Trace-Id"] = trace_id
            
            return response
            
        except Exception as e:
            # Log error
            duration = asyncio.get_event_loop().time() - start_time
            
            logger.error(
                f"Request failed: {method} {url} - {str(e)} ({duration:.3f}s)",
                extra={
                    "event": "request_error",
                    "method": method,
                    "url": url,
                    "error": str(e),
                    "duration": duration,
                    "trace_id": trace_id,
                },
                exc_info=True
            )
            raise


class HealthCheckBypassMiddleware(BaseHTTPMiddleware):
    """Bypass some middleware for health checks"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip some middleware for health endpoints
        if request.url.path in ["/health", "/health/", "/metrics"]:
            return await call_next(request)
        
        return await call_next(request)