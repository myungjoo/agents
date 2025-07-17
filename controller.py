import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import subprocess
import sys
import os
import json
from typing import Dict, List, Optional

# --- Configuration ---
APP_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(APP_DIR, "web/templates"))
app = FastAPI()

# In-memory storage for agent processes and statuses.
# For a production system, consider a database like SQLite.
agent_processes: Dict[str, subprocess.Popen] = {}
agent_statuses: Dict[str, Dict] = {}

class JobRequest(BaseModel):
    agent_name: str
    repo_url: str

def find_available_agents() -> List[str]:
    """Scans the /agents directory to find available agent modules."""
    agents_dir = os.path.join(APP_DIR, "agents")
    available = []
    for name in os.listdir(agents_dir):
        if os.path.isdir(os.path.join(agents_dir, name)) and name != "common_logic":
            available.append(name)
            if name not in agent_statuses:
                agent_statuses[name] = {"status": "stopped", "pid": None, "details": "Awaiting commands."}
    return available

# --- API Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serves the main web interface."""
    find_available_agents()
    return templates.TemplateResponse("index.html", {"request": request, "agents": agent_statuses})

@app.get("/api/agents")
async def get_agents():
    """Returns the list and status of all agents."""
    find_available_agents()
    return agent_statuses

@app.post("/api/agents/{agent_name}/start")
async def start_agent(agent_name: str):
    """Starts a specified agent as a subprocess."""
    find_available_agents()
    if agent_name not in agent_statuses:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent_statuses[agent_name]["status"] == "running":
        raise HTTPException(status_code=400, detail="Agent is already running")

    agent_path = os.path.join(APP_DIR, "agents", agent_name, "main.py")
    if not os.path.exists(agent_path):
        raise HTTPException(status_code=404, detail=f"Agent main.py not found at {agent_path}")

    # Using the same Python executable that is running the controller
    python_executable = sys.executable
    process = subprocess.Popen([python_executable, agent_path, f"--controller-url", f"http://localhost:8000"])
    
    agent_processes[agent_name] = process
    agent_statuses[agent_name] = {"status": "running", "pid": process.pid, "details": "Initializing..."}
    
    return {"message": f"Agent '{agent_name}' started successfully.", "pid": process.pid}

@app.post("/api/agents/{agent_name}/stop")
async def stop_agent(agent_name: str):
    """Stops a running agent."""
    if agent_name not in agent_processes or agent_statuses.get(agent_name, {}).get("status") != "running":
        raise HTTPException(status_code=404, detail="Agent is not running or does not exist")

    process = agent_processes[agent_name]
    process.terminate()  # Sends SIGTERM
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill() # Sends SIGKILL

    del agent_processes[agent_name]
    agent_statuses[agent_name] = {"status": "stopped", "pid": None, "details": "Terminated by user."}
    
    return {"message": f"Agent '{agent_name}' stopped."}

class StatusUpdateRequest(BaseModel):
    status: str
    details: Optional[str] = None

@app.post("/api/agents/{agent_name}/status")
async def update_agent_status(agent_name: str, status_update: StatusUpdateRequest):
    """Endpoint for agents to report their own status."""
    if agent_name not in agent_statuses:
        agent_statuses[agent_name] = {}
    
    agent_statuses[agent_name].update({
        "status": status_update.status,
        "details": status_update.details or agent_statuses[agent_name].get("details"),
        "pid": agent_statuses[agent_name].get("pid")
    })
    return {"message": "Status updated"}

@app.post("/api/jobs/run-audit")
async def run_audit_job(job: JobRequest):
    """Triggers a code audit job for a specific agent."""
    agent_name = job.agent_name
    if agent_statuses.get(agent_name, {}).get("status") != "running":
         raise HTTPException(status_code=400, detail=f"Agent '{agent_name}' is not running. Please start it first.")
    
    # In a real system, this would use a robust message queue (e.g., RabbitMQ, Redis)
    # For simplicity, we'll write the job to a temporary file the agent can poll.
    job_dir = os.path.join(APP_DIR, "jobs")
    os.makedirs(job_dir, exist_ok=True)
    job_file = os.path.join(job_dir, f"{agent_name}.job")
    with open(job_file, 'w') as f:
        json.dump({"repo_url": job.repo_url}, f)
        
    agent_statuses[agent_name]['details'] = f"New job received: Audit {job.repo_url}"
    return {"message": f"Job assigned to agent '{agent_name}' to audit {job.repo_url}"}


if __name__ == "__main__":
    # Load configuration
    import configparser
    config = configparser.ConfigParser()
    config.read('config.ini')
    host = config.get('Controller', 'host', fallback='0.0.0.0')
    port = config.getint('Controller', 'port', fallback=8000)
    
    print("Starting Agent Controller...")
    print(f"Web UI will be available at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)

