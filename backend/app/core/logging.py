import logging
import logging.handlers
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from .config import settings

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the log record.
    """
    def __init__(self, **kwargs):
        self.json_default = kwargs.pop("json_default", str)
        super().__init__(**kwargs)

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if available
        if record.exc_info:
            exc_type = record.exc_info[0]
            exc_type_name = exc_type.__name__ if exc_type else "Unknown"
            log_data["exception"] = {
                "type": exc_type_name,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add any extra attributes that were passed in
        for key, value in record.__dict__.items():
            if key not in ["args", "asctime", "created", "exc_info", "exc_text", 
                          "filename", "funcName", "id", "levelname", "levelno",
                          "lineno", "module", "msecs", "message", "msg", 
                          "name", "pathname", "process", "processName", 
                          "relativeCreated", "stack_info", "thread", "threadName"]:
                log_data[key] = value
        
        return json.dumps(log_data, default=self.json_default)


class RequestIdFilter(logging.Filter):
    """
    Filter that adds request_id to log records.
    """
    def __init__(self, request_id: Optional[str] = None):
        super().__init__()
        self.request_id = request_id or "unknown"
        
    def filter(self, record: logging.LogRecord) -> bool:
        """Add request_id to the record."""
        record.request_id = self.request_id
        return True


def setup_logging() -> None:
    """
    Set up logging configuration for the application.
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler for development
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        "logs/app.log",
        maxBytes=10485760,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_formatter = JsonFormatter()
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler for errors only
    error_file_handler = logging.handlers.RotatingFileHandler(
        "logs/error.log",
        maxBytes=10485760,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_file_handler)
    
    # Set specific loggers
    for logger_name, logger_level in [
        ("uvicorn", log_level),
        ("uvicorn.access", log_level),
        ("uvicorn.error", logging.ERROR),
        ("sqlalchemy.engine", logging.WARNING),
        ("fastapi", log_level),
    ]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logger_level)
        # Prevent propagation to avoid duplicate logs
        logger.propagate = False
        for handler in [console_handler, file_handler, error_file_handler]:
            logger.addHandler(handler)
    
    # Log startup message
    logging.info(
        f"Logging initialized with level {settings.LOG_LEVEL.upper()}",
        extra={"app_name": settings.APP_NAME, "version": settings.VERSION}
    )


def get_request_logger(request_id: str) -> logging.Logger:
    """
    Get a logger with request_id filter for request-specific logging.
    
    Args:
        request_id: Unique identifier for the request
        
    Returns:
        Logger with request_id filter
    """
    logger = logging.getLogger("app.request")
    # Remove existing request ID filters
    for filter in logger.filters[:]:
        if isinstance(filter, RequestIdFilter):
            logger.removeFilter(filter)
    
    # Add new request ID filter
    logger.addFilter(RequestIdFilter(request_id))
    return logger 