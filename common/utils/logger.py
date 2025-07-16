"""
Logging system for the AI Agent System.

Provides structured logging with different levels, file rotation,
and formatting suitable for both development and production use.
"""

import logging
import logging.handlers
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import traceback


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data, default=str)


class ColoredConsoleFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Create formatted message
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        message = f"{color}[{timestamp}] {record.levelname:8} {record.name:20} | {record.getMessage()}{reset}"
        
        if record.exc_info:
            message += f"\n{color}{self.formatException(record.exc_info)}{reset}"
        
        return message


class Logger:
    """Enhanced logger with structured logging and multiple handlers."""
    
    _loggers: Dict[str, logging.Logger] = {}
    _initialized = False
    
    def __init__(self, name: str, level: Optional[str] = None):
        self.name = name
        self.level = level or os.getenv("LOG_LEVEL", "INFO")
        
        if not Logger._initialized:
            Logger._setup_logging()
            Logger._initialized = True
        
        self.logger = self._get_logger(name)
    
    @classmethod
    def _setup_logging(cls):
        """Setup global logging configuration."""
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Set up root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ColoredConsoleFormatter())
        root_logger.addHandler(console_handler)
        
        # File handler with rotation for general logs
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "ai_agents.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
        
        # Error file handler for errors and above
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / "errors.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(error_handler)
        
        # Audit log for important events
        audit_handler = logging.handlers.RotatingFileHandler(
            log_dir / "audit.log",
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=10,
            encoding='utf-8'
        )
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(StructuredFormatter())
        
        # Create audit logger
        audit_logger = logging.getLogger("audit")
        audit_logger.setLevel(logging.INFO)
        audit_logger.addHandler(audit_handler)
        audit_logger.propagate = False
    
    def _get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger instance."""
        if name not in Logger._loggers:
            logger = logging.getLogger(name)
            logger.setLevel(getattr(logging, self.level.upper()))
            Logger._loggers[name] = logger
        
        return Logger._loggers[name]
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        kwargs['exc_info'] = True
        self._log(logging.ERROR, message, **kwargs)
    
    def audit(self, event: str, **kwargs):
        """Log audit event."""
        audit_logger = logging.getLogger("audit")
        extra_fields = {
            "event_type": event,
            "agent": self.name,
            **kwargs
        }
        
        # Create a log record with extra fields
        record = audit_logger.makeRecord(
            audit_logger.name,
            logging.INFO,
            "",
            0,
            f"Audit event: {event}",
            (),
            None
        )
        record.extra_fields = extra_fields
        audit_logger.handle(record)
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method with extra fields."""
        if kwargs:
            # Create a log record with extra fields
            record = self.logger.makeRecord(
                self.logger.name,
                level,
                "",
                0,
                message,
                (),
                kwargs.get('exc_info')
            )
            record.extra_fields = {k: v for k, v in kwargs.items() if k != 'exc_info'}
            self.logger.handle(record)
        else:
            self.logger.log(level, message)
    
    def with_context(self, **context) -> "ContextLogger":
        """Create a context logger with additional fields."""
        return ContextLogger(self, context)
    
    @classmethod
    def get_logger(cls, name: str) -> "Logger":
        """Get logger instance by name."""
        return cls(name)
    
    @classmethod
    def set_level(cls, level: str):
        """Set global logging level."""
        level_num = getattr(logging, level.upper())
        logging.getLogger().setLevel(level_num)
        
        # Update all existing loggers
        for logger in cls._loggers.values():
            logger.setLevel(level_num)


class ContextLogger:
    """Logger wrapper that adds context to all log messages."""
    
    def __init__(self, logger: Logger, context: Dict[str, Any]):
        self.logger = logger
        self.context = context
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self.logger.debug(message, **{**self.context, **kwargs})
    
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self.logger.info(message, **{**self.context, **kwargs})
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self.logger.warning(message, **{**self.context, **kwargs})
    
    def error(self, message: str, **kwargs):
        """Log error message with context."""
        self.logger.error(message, **{**self.context, **kwargs})
    
    def critical(self, message: str, **kwargs):
        """Log critical message with context."""
        self.logger.critical(message, **{**self.context, **kwargs})
    
    def exception(self, message: str, **kwargs):
        """Log exception with context."""
        self.logger.exception(message, **{**self.context, **kwargs})
    
    def audit(self, event: str, **kwargs):
        """Log audit event with context."""
        self.logger.audit(event, **{**self.context, **kwargs})