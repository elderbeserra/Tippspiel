from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
import time
import json
from typing import Callable
import structlog

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

def setup_middleware(app: FastAPI) -> None:
    """Setup all middleware for the application."""
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Trusted Host
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure this based on your domain
    )
    
    # Request ID
    @app.middleware("http")
    async def add_request_id(request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(time.time_ns()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    
    # Logging
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        logger.info(
            "request_started",
            request_id=getattr(request.state, "request_id", None),
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        
        response = await call_next(request)
        
        # Log response
        duration = time.time() - start_time
        logger.info(
            "request_finished",
            request_id=getattr(request.state, "request_id", None),
            status_code=response.status_code,
            duration=duration,
        )
        
        return response
    
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