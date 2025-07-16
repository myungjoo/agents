"""
FastAPI Web Application for AI Agent System

Provides REST API endpoints and web interface for monitoring and controlling agents.
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn
import os

from .routes import api_router, web_router
from common.utils import Config, Logger


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    config = Config()
    logger = Logger().get_logger("web_app")
    
    # Create FastAPI app
    app = FastAPI(
        title="AI Agent System",
        description="Web interface for AI code auditing agents",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Mount static files
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Setup templates
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    if os.path.exists(templates_dir):
        templates = Jinja2Templates(directory=templates_dir)
        app.state.templates = templates
    
    # Include routers
    app.include_router(api_router, prefix="/api")
    app.include_router(web_router)
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        logger.info("Web application starting up")
        
        # Initialize agent manager
        from agents.manager import AgentManager
        agent_manager = AgentManager()
        await agent_manager.initialize()
        
        # Register default agents
        await _register_default_agents(agent_manager)
        
        logger.info("Web application started successfully")
    
    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Web application shutting down")
        
        # Stop all agents
        from agents.manager import AgentManager
        agent_manager = AgentManager()
        await agent_manager.stop_all_agents()
        
        logger.info("Web application shutdown complete")
    
    return app


async def _register_default_agents(agent_manager):
    """Register default agents with the manager."""
    from agents.repository_analyzer import RepositoryAnalyzer
    from agents.issue_detector import IssueDetector
    from agents.code_fixer import CodeFixer
    from agents.test_runner import TestRunner
    from agents.report_generator import ReportGenerator
    from agents.pr_creator import PRCreator
    
    # Create and register agents
    agents = [
        RepositoryAnalyzer(),
        IssueDetector(),
        CodeFixer(),
        TestRunner(),
        ReportGenerator(),
        PRCreator()
    ]
    
    for agent in agents:
        agent_manager.register_agent(agent)


def run_web_server():
    """Run the web server."""
    config = Config()
    
    web_config = config.get_web_config()
    host = web_config.get('host', '0.0.0.0')
    port = web_config.get('port', 8080)
    
    app = create_app()
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    run_web_server()