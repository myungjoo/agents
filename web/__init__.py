"""
Web Interface for AI Agent System

Provides a modern web UI for monitoring and controlling AI agents.
"""

from .app import create_app
from .routes import api_router, web_router

__all__ = ['create_app', 'api_router', 'web_router']