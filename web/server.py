#!/usr/bin/env python3
"""
Web Server for AI Agent System
Provides real-time dashboard for monitoring and controlling agents
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

import uvicorn
from fastapi import FastAPI, WebSocket, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import websockets

from common.config import ConfigManager
from common.utils.logging import setup_logging, get_agent_logger


logger = get_agent_logger("web_server")

# Global application state
app_state = {
    'config': None,
    'connected_clients': set(),
    'agents': {
        'repo_analyzer': {'status': 'idle', 'tasks_completed': 0},
        'issue_finder': {'status': 'idle', 'tasks_completed': 0},
        'code_tester': {'status': 'idle', 'tasks_completed': 0},
        'report_generator': {'status': 'idle', 'tasks_completed': 0}
    }
}


def create_app(config: ConfigManager) -> FastAPI:
    """Create FastAPI application"""
    app = FastAPI(
        title="AI Agent System Dashboard",
        description="Real-time monitoring and control for AI code audit agents",
        version="1.0.0"
    )
    
    # Store config in app state
    app_state['config'] = config
    
    # Setup static files and templates
    web_dir = Path(__file__).parent
    app.mount("/static", StaticFiles(directory=web_dir / "static"), name="static")
    templates = Jinja2Templates(directory=web_dir / "templates")
    
    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        """Main dashboard page"""
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "title": "AI Agent System Dashboard",
            "agents": app_state['agents']
        })
    
    @app.get("/api/status")
    async def get_status():
        """Get system status"""
        return {
            "status": "running",
            "agents": app_state['agents'],
            "connected_clients": len(app_state['connected_clients']),
            "system": {
                "name": config.get("system.name", "AI Agent System"),
                "version": config.get("system.version", "1.0.0"),
                "environment": config.get("system.environment", "development")
            }
        }
    
    @app.get("/api/agents")
    async def get_agents():
        """Get all agents status"""
        return {"agents": app_state['agents']}
    
    @app.get("/api/agents/{agent_id}")
    async def get_agent(agent_id: str):
        """Get specific agent status"""
        if agent_id not in app_state['agents']:
            raise HTTPException(status_code=404, detail="Agent not found")
        return {"agent": app_state['agents'][agent_id]}
    
    @app.post("/api/agents/{agent_id}/start")
    async def start_agent(agent_id: str):
        """Start an agent"""
        if agent_id not in app_state['agents']:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        app_state['agents'][agent_id]['status'] = 'running'
        await broadcast_update({'type': 'agent_status', 'agent_id': agent_id, 'status': 'running'})
        return {"message": f"Agent {agent_id} started"}
    
    @app.post("/api/agents/{agent_id}/stop")
    async def stop_agent(agent_id: str):
        """Stop an agent"""
        if agent_id not in app_state['agents']:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        app_state['agents'][agent_id]['status'] = 'stopped'
        await broadcast_update({'type': 'agent_status', 'agent_id': agent_id, 'status': 'stopped'})
        return {"message": f"Agent {agent_id} stopped"}
    
    @app.post("/api/analyze")
    async def analyze_repository(request: Request):
        """Analyze a repository"""
        data = await request.json()
        repo_url = data.get('repository_url')
        
        if not repo_url:
            raise HTTPException(status_code=400, detail="Repository URL required")
        
        # Simulate analysis task
        task_id = f"task_{len(app_state.get('tasks', []))}"
        
        # In a real implementation, this would queue the task for agents
        await broadcast_update({
            'type': 'task_started',
            'task_id': task_id,
            'repository_url': repo_url
        })
        
        return {"task_id": task_id, "message": "Analysis started"}
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time updates"""
        await websocket.accept()
        app_state['connected_clients'].add(websocket)
        
        try:
            # Send initial state
            await websocket.send_json({
                'type': 'initial_state',
                'agents': app_state['agents']
            })
            
            # Keep connection alive
            while True:
                try:
                    # Wait for messages from client
                    message = await websocket.receive_json()
                    logger.debug(f"Received WebSocket message: {message}")
                except:
                    break
                
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            app_state['connected_clients'].discard(websocket)
    
    return app


async def broadcast_update(message: Dict[str, Any]):
    """Broadcast update to all connected clients"""
    if app_state['connected_clients']:
        # Create tasks for all clients
        tasks = []
        for client in app_state['connected_clients'].copy():
            tasks.append(send_to_client(client, message))
        
        # Send to all clients concurrently
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


async def send_to_client(websocket: WebSocket, message: Dict[str, Any]):
    """Send message to a specific client"""
    try:
        await websocket.send_json(message)
    except Exception as e:
        logger.warning(f"Failed to send message to client: {e}")
        app_state['connected_clients'].discard(websocket)


def main():
    """Main entry point for web server"""
    parser = argparse.ArgumentParser(description="AI Agent System Web Server")
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Host to bind to"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind to"
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = ConfigManager(args.config)
        
        # Setup logging
        log_config = config.get_section("logging")
        setup_logging(
            level=log_config.get("level", "INFO"),
            format_type=log_config.get("format", "structured"),
            log_file=log_config.get("file")
        )
        
        # Get web configuration
        web_config = config.get_section("web")
        host = args.host or web_config.get("host", "127.0.0.1")
        port = args.port or web_config.get("port", 8080)
        
        # Create app
        app = create_app(config)
        
        logger.info(f"Starting web server on {host}:{port}")
        
        # Run server
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=log_config.get("level", "info").lower()
        )
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Web server failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()