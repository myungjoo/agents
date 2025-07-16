"""
Common utilities and shared components for AI Agent System
"""

__version__ = "1.0.0"
__author__ = "AI Code Audit Team"
__license__ = "MIT"

from .config import ConfigManager
from .utils import logger, setup_logging
from .llm import LLMManager
from .mcp import MCPClient, MCPServer
from .a2a import A2AManager

__all__ = [
    "ConfigManager",
    "logger", 
    "setup_logging",
    "LLMManager",
    "MCPClient",
    "MCPServer", 
    "A2AManager"
]