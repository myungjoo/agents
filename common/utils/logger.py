"""
Logging utility for the AI Agent System.
"""

import logging
import structlog
import sys
from typing import Optional
import os
from datetime import datetime


class Logger:
    """Centralized logging for the AI Agent System."""
    
    _instance: Optional['Logger'] = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_logging()
            Logger._initialized = True
    
    def _setup_logging(self):
        """Setup structured logging."""
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # Get log level from environment
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        log_file = os.getenv('LOG_FILE', '/var/log/ai_agents/system.log')
        
        # Create logger
        self.logger = structlog.get_logger()
        
        # Setup handlers
        self._setup_handlers(log_level, log_file)
    
    def _setup_handlers(self, log_level: str, log_file: str):
        """Setup log handlers."""
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level))
        
        # File handler
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, log_level))
        except Exception as e:
            print(f"Warning: Could not setup file logging to {log_file}: {e}")
            file_handler = None
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level))
        root_logger.addHandler(console_handler)
        
        if file_handler:
            root_logger.addHandler(file_handler)
    
    def get_logger(self, name: str = None) -> structlog.BoundLogger:
        """Get a logger instance."""
        if name:
            return structlog.get_logger(name)
        return self.logger
    
    def log_agent_start(self, agent_name: str, agent_id: str, **kwargs):
        """Log agent start event."""
        self.logger.info(
            "Agent started",
            agent_name=agent_name,
            agent_id=agent_id,
            event="agent_start",
            **kwargs
        )
    
    def log_agent_stop(self, agent_name: str, agent_id: str, **kwargs):
        """Log agent stop event."""
        self.logger.info(
            "Agent stopped",
            agent_name=agent_name,
            agent_id=agent_id,
            event="agent_stop",
            **kwargs
        )
    
    def log_agent_error(self, agent_name: str, agent_id: str, error: str, **kwargs):
        """Log agent error."""
        self.logger.error(
            "Agent error",
            agent_name=agent_name,
            agent_id=agent_id,
            error=error,
            event="agent_error",
            **kwargs
        )
    
    def log_llm_call(self, provider: str, model: str, response_time: float, **kwargs):
        """Log LLM API call."""
        self.logger.info(
            "LLM call completed",
            provider=provider,
            model=model,
            response_time=response_time,
            event="llm_call",
            **kwargs
        )
    
    def log_audit_start(self, repository: str, branch: str, **kwargs):
        """Log audit start event."""
        self.logger.info(
            "Audit started",
            repository=repository,
            branch=branch,
            event="audit_start",
            **kwargs
        )
    
    def log_audit_complete(self, repository: str, branch: str, issues_found: int, **kwargs):
        """Log audit completion."""
        self.logger.info(
            "Audit completed",
            repository=repository,
            branch=branch,
            issues_found=issues_found,
            event="audit_complete",
            **kwargs
        )
    
    def log_performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics."""
        self.logger.info(
            "Performance metric",
            operation=operation,
            duration=duration,
            event="performance",
            **kwargs
        )