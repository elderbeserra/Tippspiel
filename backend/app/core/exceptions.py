from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable
import logging

logger = logging.getLogger(__name__)

class BaseAPIException(HTTPException):
    """Base class for all API exceptions with standardized error response format."""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = "general_error",
        headers: Optional[Dict[str, str]] = None,
        extra: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.extra = extra or {}
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class NotFoundException(BaseAPIException):
    """Exception raised when a requested resource is not found."""
    
    def __init__(
        self,
        detail: str = "Resource not found",
        error_code: str = "not_found",
        resource_type: Optional[str] = None,
        resource_id: Optional[Union[str, int]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        extra = {}
        if resource_type:
            extra["resource_type"] = resource_type
        if resource_id:
            extra["resource_id"] = resource_id
            
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code=error_code,
            headers=headers,
            extra=extra
        )


class AuthenticationException(BaseAPIException):
    """Exception raised for authentication errors."""
    
    def __init__(
        self,
        detail: str = "Authentication failed",
        error_code: str = "authentication_error",
        headers: Optional[Dict[str, str]] = None
    ):
        headers = headers or {"WWW-Authenticate": "Bearer"}
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code=error_code,
            headers=headers
        )


class AuthorizationException(BaseAPIException):
    """Exception raised for authorization errors."""
    
    def __init__(
        self,
        detail: str = "Not authorized to perform this action",
        error_code: str = "authorization_error",
        required_role: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        extra = {}
        if required_role:
            extra["required_role"] = required_role
            
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
            headers=headers,
            extra=extra
        )


class ValidationException(BaseAPIException):
    """Exception raised for data validation errors."""
    
    def __init__(
        self,
        detail: str = "Validation error",
        error_code: str = "validation_error",
        field_errors: Optional[Dict[str, List[str]]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        extra = {}
        if field_errors:
            extra["field_errors"] = field_errors
            
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code=error_code,
            headers=headers,
            extra=extra
        )


class DatabaseException(BaseAPIException):
    """Exception raised for database errors."""
    
    def __init__(
        self,
        detail: str = "Database error",
        error_code: str = "database_error",
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code=error_code,
            headers=headers
        )


class BusinessLogicException(BaseAPIException):
    """Exception raised for business logic errors."""
    
    def __init__(
        self,
        detail: str,
        error_code: str = "business_logic_error",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        headers: Optional[Dict[str, str]] = None,
        extra: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status_code,
            detail=detail,
            error_code=error_code,
            headers=headers,
            extra=extra
        )


# Type alias for FastAPI exception handlers
ExceptionHandler = Callable[[Request, Any], Awaitable[JSONResponse]]

async def api_exception_handler(request: Request, exc: BaseAPIException) -> JSONResponse:
    """Handler for custom API exceptions."""
    content = {
        "error": {
            "code": exc.error_code,
            "message": exc.detail,
            "status_code": exc.status_code,
        }
    }
    
    if exc.extra:
        content["error"]["details"] = exc.extra
        
    # Log the error
    logger.error(
        f"API Exception: {exc.error_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "client_host": request.client.host if request.client else None,
            "extra": exc.extra
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler for request validation errors."""
    field_errors = {}
    
    for error in exc.errors():
        loc = error.get("loc", [])
        if len(loc) > 1:  # First item is typically 'body', 'query', etc.
            field = ".".join(str(item) for item in loc[1:])
            msg = error.get("msg", "Validation error")
            
            if field in field_errors:
                field_errors[field].append(msg)
            else:
                field_errors[field] = [msg]
    
    content = {
        "error": {
            "code": "validation_error",
            "message": "Request validation failed",
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "details": {
                "field_errors": field_errors
            }
        }
    }
    
    # Log the error
    logger.error(
        f"Validation Error: {field_errors}",
        extra={
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "path": request.url.path,
            "method": request.method,
            "client_host": request.client.host if request.client else None,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=content
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handler for standard HTTP exceptions."""
    content = {
        "error": {
            "code": "http_error",
            "message": exc.detail,
            "status_code": exc.status_code,
        }
    }
    
    # Log the error
    logger.error(
        f"HTTP Exception: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "client_host": request.client.host if request.client else None,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for unhandled exceptions."""
    content = {
        "error": {
            "code": "internal_server_error",
            "message": "An unexpected error occurred",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        }
    }
    
    # Log the error with full traceback
    logger.exception(
        f"Unhandled Exception: {str(exc)}",
        extra={
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "path": request.url.path,
            "method": request.method,
            "client_host": request.client.host if request.client else None,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=content
    ) 