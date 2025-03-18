from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
import time
import json
from typing import Callable
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import uuid
import logging
from .logging import get_request_logger

from .config import settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging request information and adding request ID.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Get request-specific logger
        request_logger = get_request_logger(request_id)
        
        # Log request start
        start_time = time.time()
        request_logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_host": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent", ""),
            }
        )
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log request completion
            request_logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time_ms": round(process_time * 1000, 2),
                }
            )
            
            return response
            
        except Exception as e:
            # Log exception
            process_time = time.time() - start_time
            request_logger.exception(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "process_time_ms": round(process_time * 1000, 2),
                }
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting requests.
    """
    
    def __init__(self, app: ASGIApp, rate_limit_per_minute: int = 60):
        super().__init__(app)
        self.rate_limit_per_minute = rate_limit_per_minute
        self.requests = {}
        
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip rate limiting for certain paths
        if request.url.path.startswith("/api/v1/docs") or request.url.path.startswith("/api/v1/redoc"):
            return await call_next(request)
        
        # Check if client has exceeded rate limit
        current_time = time.time()
        if client_ip in self.requests:
            # Clean up old requests
            self.requests[client_ip] = [t for t in self.requests[client_ip] if current_time - t < 60]
            
            # Check rate limit
            if len(self.requests[client_ip]) >= self.rate_limit_per_minute:
                logger.warning(
                    f"Rate limit exceeded for {client_ip}",
                    extra={
                        "client_ip": client_ip,
                        "path": request.url.path,
                        "method": request.method,
                    }
                )
                return Response(
                    content="Rate limit exceeded. Please try again later.",
                    status_code=429,
                    headers={"Retry-After": "60"}
                )
                
        # Add request timestamp
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append(current_time)
        
        # Process the request
        return await call_next(request)

def setup_middleware(app: FastAPI) -> None:
    """Setup all middleware for the application."""
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["Content-Type", "Set-Cookie", "Access-Control-Allow-Headers", 
                      "Access-Control-Allow-Origin", "Authorization"],
        expose_headers=["Content-Type", "Set-Cookie"],
        max_age=600,  # 10 minutes
    )
    
    # Trusted Host
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure this based on your domain
    )
    
    # Request ID and logging
    app.add_middleware(RequestLoggingMiddleware)
    
    # Rate limiting
    app.add_middleware(
        RateLimitMiddleware,
        rate_limit_per_minute=settings.RATE_LIMIT_PER_MINUTE
    )
    
    # Error handling
    @app.middleware("http")
    async def error_handling_middleware(request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            logger.exception(
                "unhandled_error",
                request_id=getattr(request.state, "request_id", None),
                error=str(e),
                error_type=type(e).__name__,
            )
            return Response(
                content=json.dumps({
                    "detail": "Internal server error",
                    "request_id": getattr(request.state, "request_id", None)
                }),
                status_code=500,
                media_type="application/json"
            ) 