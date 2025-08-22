"""
Comprehensive logging configuration for the stock scanner application.
Provides structured logging with different levels and output formats.
"""

import logging
import logging.handlers
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info']:
                log_data[key] = value
        
        return json.dumps(log_data, default=str)


class ContextFilter(logging.Filter):
    """Filter to add context information to log records."""
    
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.context = context or {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record."""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_json_logging: bool = True,
    enable_console_logging: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Set up comprehensive logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        enable_json_logging: Whether to use JSON format for file logging
        enable_console_logging: Whether to enable console logging
        max_file_size: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
    """
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if enable_console_logging:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        
        # Use simple format for console
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        file_handler.setLevel(numeric_level)
        
        # Use JSON format for file logging if enabled
        if enable_json_logging:
            file_formatter = JSONFormatter()
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
        
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("yfinance").setLevel(logging.WARNING)


def get_logger(name: str, context: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """
    Get a logger with optional context.
    
    Args:
        name: Logger name
        context: Additional context to include in all log messages
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if context:
        # Add context filter
        context_filter = ContextFilter(context)
        logger.addFilter(context_filter)
    
    return logger


class LoggingContext:
    """Context manager for adding temporary context to logs."""
    
    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context
        self.filter = None
    
    def __enter__(self):
        self.filter = ContextFilter(self.context)
        self.logger.addFilter(self.filter)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.filter:
            self.logger.removeFilter(self.filter)


class PerformanceLogger:
    """Logger for performance monitoring."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.start_time = None
        self.operation = None
    
    def start(self, operation: str, **context):
        """Start timing an operation."""
        self.operation = operation
        self.start_time = datetime.utcnow()
        
        self.logger.info(
            f"Starting operation: {operation}",
            extra={
                "operation": operation,
                "operation_status": "started",
                **context
            }
        )
    
    def end(self, success: bool = True, **context):
        """End timing an operation."""
        if self.start_time is None:
            return
        
        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds()
        
        status = "completed" if success else "failed"
        level = logging.INFO if success else logging.ERROR
        
        self.logger.log(
            level,
            f"Operation {status}: {self.operation} (duration: {duration:.3f}s)",
            extra={
                "operation": self.operation,
                "operation_status": status,
                "duration_seconds": duration,
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                **context
            }
        )
        
        # Reset
        self.start_time = None
        self.operation = None


def log_function_call(logger: logging.Logger):
    """Decorator to log function calls with parameters and results."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            
            # Log function entry
            logger.debug(
                f"Entering function: {func_name}",
                extra={
                    "function": func_name,
                    "function_status": "entering",
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys())
                }
            )
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Log successful exit
                logger.debug(
                    f"Exiting function: {func_name}",
                    extra={
                        "function": func_name,
                        "function_status": "success",
                        "has_result": result is not None
                    }
                )
                
                return result
                
            except Exception as exc:
                # Log exception
                logger.error(
                    f"Function failed: {func_name}",
                    extra={
                        "function": func_name,
                        "function_status": "error",
                        "exception_type": type(exc).__name__,
                        "exception_message": str(exc)
                    },
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


# Initialize logging on module import
def initialize_application_logging():
    """Initialize logging for the application."""
    # Get configuration from environment
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", "logs/stock_scanner.log")
    enable_json = os.getenv("ENABLE_JSON_LOGGING", "true").lower() == "true"
    enable_console = os.getenv("ENABLE_CONSOLE_LOGGING", "true").lower() == "true"
    
    # Set up logging
    setup_logging(
        log_level=log_level,
        log_file=log_file,
        enable_json_logging=enable_json,
        enable_console_logging=enable_console
    )
    
    # Log initialization
    logger = get_logger(__name__)
    logger.info(
        "Logging initialized",
        extra={
            "log_level": log_level,
            "log_file": log_file,
            "json_logging": enable_json,
            "console_logging": enable_console
        }
    )


# Auto-initialize if not in test environment
if not os.getenv("TESTING"):
    initialize_application_logging()