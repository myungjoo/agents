"""
Common utilities and shared components for the AI Agent System.

This module provides shared functionality across all agents including:
- LLM provider management
- Database connections
- Utility functions
- Configuration management
- MCP and A2A communication protocols
"""

__version__ = "1.0.0"
__author__ = "AI Agent System"

from .llm import LLMManager, LLMProvider
from .utils import Logger, Config, DatabaseManager
from .mcp import MCPClient, MCPServer
from .a2a import A2AManager, A2AMessage

__all__ = [
    "LLMManager",
    "LLMProvider", 
    "Logger",
    "Config",
    "DatabaseManager",
    "MCPClient",
    "MCPServer",
    "A2AManager",
    "A2AMessage"
]