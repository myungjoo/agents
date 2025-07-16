#!/usr/bin/env python3
"""
Logging configuration for AI Agent System
Provides structured logging with multiple output formats
"""

import logging
import sys
import json
from pathlib import Path
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler
import structlog


# Global logger instance
logger = structlog.get_logger()


def setup_logging(
    level: str = "INFO",
    format_type: str = "structured",
    log_file: Optional[str] = None,
    max_size: str = "100MB",
    backup_count: int = 5
) -> None:
    """
    Setup structured logging for the system
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Format type (simple, structured)
        log_file: Path to log file (optional)
        max_size: Maximum log file size
        backup_count: Number of backup files to keep
    """
    # Convert level string to logging level
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure stdlib logging
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        handlers=[]
    )
    
    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if format_type == "structured":
        processors.append(structlog.processors.JSONRenderer())
        formatter = StructuredFormatter()
    else:
        processors.append(structlog.dev.ConsoleRenderer())
        formatter = SimpleFormatter()
    
    # Configure handlers
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Parse max_size
        max_bytes = _parse_size(max_size)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers = handlers
    root_logger.setLevel(log_level)
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    logger.info("Logging configured", level=level, format=format_type)


def _parse_size(size_str: str) -> int:
    """Parse size string to bytes"""
    size_str = size_str.upper()
    if size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    elif size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    else:
        return int(size_str)


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for log records"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra') and record.extra:
            log_data.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class SimpleFormatter(logging.Formatter):
    """Simple text formatter for log records"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


class AgentLogger:
    """Logger wrapper for agent-specific logging"""
    
    def __init__(self, agent_name: str):
        """
        Initialize agent logger
        
        Args:
            agent_name: Name of the agent
        """
        self.agent_name = agent_name
        self.logger = structlog.get_logger().bind(agent=agent_name)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, **kwargs)
    
    def log_task_start(self, task_name: str, **kwargs):
        """Log task start"""
        self.info(f"Task started: {task_name}", task=task_name, status="started", **kwargs)
    
    def log_task_complete(self, task_name: str, duration: float = None, **kwargs):
        """Log task completion"""
        log_data = {"task": task_name, "status": "completed"}
        if duration is not None:
            log_data["duration"] = duration
        log_data.update(kwargs)
        self.info(f"Task completed: {task_name}", **log_data)
    
    def log_task_error(self, task_name: str, error: Exception, **kwargs):
        """Log task error"""
        self.error(
            f"Task failed: {task_name}",
            task=task_name,
            status="failed",
            error=str(error),
            error_type=type(error).__name__,
            **kwargs
        )


def get_agent_logger(agent_name: str) -> AgentLogger:
    """
    Get agent-specific logger
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        AgentLogger instance
    """
    return AgentLogger(agent_name)