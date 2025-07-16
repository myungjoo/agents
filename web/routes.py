"""
API and Web Routes for AI Agent System

Defines REST API endpoints and web page routes for the system.
"""

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
import os
import asyncio

from agents.manager import AgentManager
from common.utils import Config, Logger


# API Models
class AuditRequest(BaseModel):
    repository: str
    branch: str = "main"


class AuditResponse(BaseModel):
    audit_id: str
    status: str
    message: str


class AgentStatusResponse(BaseModel):
    agent_id: str
    name: str
    type: str
    status: str
    execution_time: Optional[float] = None
    llm_calls: int
    total_llm_time: float


# API Router
api_router = APIRouter()


@api_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ai_agent_system"}


@api_router.get("/stats")
async def get_system_stats():
    """Get system statistics."""
    agent_manager = AgentManager()
    return agent_manager.get_system_stats()


@api_router.post("/audit", response_model=AuditResponse)
async def start_audit(request: AuditRequest, background_tasks: BackgroundTasks):
    """Start a new code audit."""
    try:
        agent_manager = AgentManager()
        audit_id = await agent_manager.start_audit(request.repository, request.branch)
        
        return AuditResponse(
            audit_id=audit_id,
            status="started",
            message=f"Audit started for {request.repository}:{request.branch}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/audit/{audit_id}")
async def get_audit_status(audit_id: str):
    """Get status of a specific audit."""
    agent_manager = AgentManager()
    status = agent_manager.get_audit_status(audit_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    return status


@api_router.get("/audits")
async def get_all_audits():
    """Get status of all audits."""
    agent_manager = AgentManager()
    return agent_manager.get_all_audit_statuses()


@api_router.delete("/audit/{audit_id}")
async def stop_audit(audit_id: str):
    """Stop a running audit."""
    try:
        agent_manager = AgentManager()
        await agent_manager.stop_audit(audit_id)
        return {"message": f"Audit {audit_id} stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/agents")
async def get_all_agents():
    """Get status of all agents."""
    agent_manager = AgentManager()
    return agent_manager.get_all_agent_statuses()


@api_router.get("/agents/{agent_id}")
async def get_agent_status(agent_id: str):
    """Get status of a specific agent."""
    agent_manager = AgentManager()
    status = agent_manager.get_agent_status(agent_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return status


@api_router.post("/agents/{agent_id}/stop")
async def stop_agent(agent_id: str):
    """Stop a specific agent."""
    agent_manager = AgentManager()
    agent = agent_manager.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent.stop()
    return {"message": f"Agent {agent_id} stopped"}


@api_router.get("/llm/providers")
async def get_llm_providers():
    """Get available LLM providers."""
    from common.llm import LLMFactory
    return LLMFactory.get_available_providers()


@api_router.post("/llm/providers/{provider}/test")
async def test_llm_provider(provider: str):
    """Test an LLM provider."""
    from common.llm import LLMFactory
    result = LLMFactory.test_provider(provider)
    return result


@api_router.post("/llm/providers/{provider}/switch")
async def switch_primary_provider(provider: str):
    """Switch the primary LLM provider."""
    from common.llm import LLMFactory
    success = LLMFactory.switch_primary_provider(provider)
    
    if success:
        return {"message": f"Switched to {provider} as primary provider"}
    else:
        raise HTTPException(status_code=400, detail=f"Failed to switch to {provider}")


@api_router.get("/config")
async def get_config():
    """Get system configuration (non-sensitive)."""
    config = Config()
    return {
        "system": config.get_system_config(),
        "web": config.get_web_config(),
        "agents": config.get_agent_config(),
        "analysis": config.get("analysis"),
        "testing": config.get("testing")
    }


@api_router.get("/config/validation")
async def validate_config():
    """Validate system configuration."""
    config = Config()
    return config.validate_config()


@api_router.get("/audit/{audit_id}/export")
async def export_audit_results(audit_id: str):
    """Export audit results."""
    agent_manager = AgentManager()
    config = Config()
    
    export_file = f"{config.get('system.data_dir')}/exports/{audit_id}_export.json"
    os.makedirs(os.path.dirname(export_file), exist_ok=True)
    
    success = agent_manager.export_audit_results(audit_id, export_file)
    
    if success:
        return {"message": f"Audit results exported to {export_file}"}
    else:
        raise HTTPException(status_code=404, detail="Audit not found or export failed")


# Web Router
web_router = APIRouter()


@web_router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    templates = request.app.state.templates
    return templates.TemplateResponse("dashboard.html", {"request": request})


@web_router.get("/audits", response_class=HTMLResponse)
async def audits_page(request: Request):
    """Audits management page."""
    templates = request.app.state.templates
    return templates.TemplateResponse("audits.html", {"request": request})


@web_router.get("/agents", response_class=HTMLResponse)
async def agents_page(request: Request):
    """Agents monitoring page."""
    templates = request.app.state.templates
    return templates.TemplateResponse("agents.html", {"request": request})


@web_router.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    """Configuration page."""
    templates = request.app.state.templates
    return templates.TemplateResponse("config.html", {"request": request})


@web_router.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """Logs viewing page."""
    templates = request.app.state.templates
    return templates.TemplateResponse("logs.html", {"request": request})


# WebSocket endpoints for real-time updates
@web_router.websocket("/ws/audits")
async def websocket_audits(websocket):
    """WebSocket endpoint for real-time audit updates."""
    await websocket.accept()
    
    try:
        while True:
            # Send audit updates every 5 seconds
            agent_manager = AgentManager()
            audits = agent_manager.get_all_audit_statuses()
            
            await websocket.send_text(json.dumps({
                "type": "audit_update",
                "data": audits
            }))
            
            await asyncio.sleep(5)
    except Exception as e:
        logger = Logger().get_logger("websocket")
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()


@web_router.websocket("/ws/agents")
async def websocket_agents(websocket):
    """WebSocket endpoint for real-time agent updates."""
    await websocket.accept()
    
    try:
        while True:
            # Send agent updates every 3 seconds
            agent_manager = AgentManager()
            agents = agent_manager.get_all_agent_statuses()
            
            await websocket.send_text(json.dumps({
                "type": "agent_update",
                "data": agents
            }))
            
            await asyncio.sleep(3)
    except Exception as e:
        logger = Logger().get_logger("websocket")
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()


@web_router.websocket("/ws/stats")
async def websocket_stats(websocket):
    """WebSocket endpoint for real-time system statistics."""
    await websocket.accept()
    
    try:
        while True:
            # Send system stats every 10 seconds
            agent_manager = AgentManager()
            stats = agent_manager.get_system_stats()
            
            await websocket.send_text(json.dumps({
                "type": "stats_update",
                "data": stats
            }))
            
            await asyncio.sleep(10)
    except Exception as e:
        logger = Logger().get_logger("websocket")
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()