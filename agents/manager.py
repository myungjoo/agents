"""
Agent Manager

Coordinates and manages all AI agents in the system, handling
agent lifecycle, communication, and resource management.
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os

from .base import BaseAgent, AgentStatus, AgentType, AgentContext, AgentResult
from common.utils import Logger, Config
from common.llm import LLMFactory


class AgentManager:
    """Manager for coordinating all AI agents."""
    
    _instance: Optional['AgentManager'] = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.agents: Dict[str, BaseAgent] = {}
            self.running_audits: Dict[str, Dict[str, Any]] = {}
            self.logger = Logger().get_logger("agent_manager")
            self.config = Config()
            self.max_concurrent_agents = self.config.get('agents.max_concurrent', 5)
            self.agent_timeout = self.config.get('agents.timeout', 3600)
            
            AgentManager._initialized = True
    
    async def initialize(self):
        """Initialize the agent manager."""
        # Initialize LLM providers
        LLMFactory.initialize_from_env()
        
        # Create data directories
        data_dir = self.config.get('system.data_dir', '/var/lib/ai_agents')
        os.makedirs(f"{data_dir}/audits", exist_ok=True)
        os.makedirs(f"{data_dir}/results", exist_ok=True)
        os.makedirs(f"{data_dir}/logs", exist_ok=True)
        
        self.logger.info("Agent manager initialized")
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent with the manager."""
        self.agents[agent.agent_id] = agent
        self.logger.info(f"Registered agent: {agent.name} ({agent.agent_id})")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)
    
    def get_agents_by_type(self, agent_type: AgentType) -> List[BaseAgent]:
        """Get all agents of a specific type."""
        return [agent for agent in self.agents.values() if agent.agent_type == agent_type]
    
    def get_running_agents(self) -> List[BaseAgent]:
        """Get all currently running agents."""
        return [agent for agent in self.agents.values() if agent.status == AgentStatus.RUNNING]
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific agent."""
        agent = self.get_agent(agent_id)
        if agent:
            return agent.get_status()
        return None
    
    def get_all_agent_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all agents."""
        return {agent_id: agent.get_status() for agent_id, agent in self.agents.items()}
    
    async def start_audit(self, repository_url: str, branch: str = "main") -> str:
        """Start a new code audit."""
        audit_id = str(uuid.uuid4())
        
        # Create audit context
        working_dir = f"{self.config.get('system.data_dir')}/audits/{audit_id}"
        os.makedirs(working_dir, exist_ok=True)
        
        context = AgentContext(
            audit_id=audit_id,
            repository_url=repository_url,
            branch=branch,
            working_directory=working_dir
        )
        
        # Store audit information
        self.running_audits[audit_id] = {
            'repository_url': repository_url,
            'branch': branch,
            'start_time': datetime.utcnow(),
            'status': 'running',
            'context': context,
            'agent_results': {}
        }
        
        self.logger.info(f"Started audit {audit_id} for {repository_url}:{branch}")
        
        # Start the audit pipeline
        asyncio.create_task(self._run_audit_pipeline(audit_id))
        
        return audit_id
    
    async def _run_audit_pipeline(self, audit_id: str):
        """Run the complete audit pipeline."""
        audit_info = self.running_audits.get(audit_id)
        if not audit_info:
            self.logger.error(f"Audit {audit_id} not found")
            return
        
        context = audit_info['context']
        
        try:
            # Step 1: Repository Analysis
            await self._run_agent_pipeline_step(audit_id, AgentType.REPOSITORY_ANALYZER, context)
            
            # Step 2: Issue Detection
            await self._run_agent_pipeline_step(audit_id, AgentType.ISSUE_DETECTOR, context)
            
            # Step 3: Code Fixing (for each issue)
            await self._run_agent_pipeline_step(audit_id, AgentType.CODE_FIXER, context)
            
            # Step 4: Test Running (for each fix)
            await self._run_agent_pipeline_step(audit_id, AgentType.TEST_RUNNER, context)
            
            # Step 5: Report Generation
            await self._run_agent_pipeline_step(audit_id, AgentType.REPORT_GENERATOR, context)
            
            # Step 6: PR Creation
            await self._run_agent_pipeline_step(audit_id, AgentType.PR_CREATOR, context)
            
            # Mark audit as completed
            audit_info['status'] = 'completed'
            audit_info['end_time'] = datetime.utcnow()
            
            self.logger.info(f"Audit {audit_id} completed successfully")
            
        except Exception as e:
            audit_info['status'] = 'failed'
            audit_info['error'] = str(e)
            audit_info['end_time'] = datetime.utcnow()
            
            self.logger.error(f"Audit {audit_id} failed: {e}")
    
    async def _run_agent_pipeline_step(self, audit_id: str, agent_type: AgentType, context: AgentContext):
        """Run a specific agent pipeline step."""
        agents = self.get_agents_by_type(agent_type)
        
        if not agents:
            self.logger.warning(f"No agents found for type {agent_type.value}")
            return
        
        # Use the first available agent of this type
        agent = agents[0]
        
        # Check if we can run more agents
        running_count = len(self.get_running_agents())
        if running_count >= self.max_concurrent_agents:
            self.logger.info(f"Waiting for agent slot (running: {running_count})")
            # Wait for a slot to become available
            while len(self.get_running_agents()) >= self.max_concurrent_agents:
                await asyncio.sleep(1)
        
        # Run the agent
        result = await agent.run(context)
        
        # Store the result
        self.running_audits[audit_id]['agent_results'][agent_type.value] = result
        context.agent_results[agent_type.value] = result
        
        # Save result to file
        result_file = f"{self.config.get('system.data_dir')}/results/{audit_id}_{agent_type.value}.json"
        agent.save_result(result_file)
        
        if not result.success:
            raise Exception(f"Agent {agent.name} failed: {result.error}")
    
    async def stop_audit(self, audit_id: str):
        """Stop a running audit."""
        audit_info = self.running_audits.get(audit_id)
        if not audit_info:
            self.logger.warning(f"Audit {audit_id} not found")
            return
        
        # Stop all running agents for this audit
        for agent in self.get_running_agents():
            if agent.context and agent.context.audit_id == audit_id:
                agent.stop()
        
        audit_info['status'] = 'stopped'
        audit_info['end_time'] = datetime.utcnow()
        
        self.logger.info(f"Stopped audit {audit_id}")
    
    def get_audit_status(self, audit_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific audit."""
        audit_info = self.running_audits.get(audit_id)
        if not audit_info:
            return None
        
        return {
            'audit_id': audit_id,
            'repository_url': audit_info['repository_url'],
            'branch': audit_info['branch'],
            'status': audit_info['status'],
            'start_time': audit_info['start_time'].isoformat(),
            'end_time': audit_info.get('end_time', '').isoformat() if audit_info.get('end_time') else None,
            'error': audit_info.get('error'),
            'agent_results': {
                agent_type: {
                    'success': result.success,
                    'execution_time': result.execution_time,
                    'error': result.error
                }
                for agent_type, result in audit_info['agent_results'].items()
            }
        }
    
    def get_all_audit_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all audits."""
        return {
            audit_id: self.get_audit_status(audit_id)
            for audit_id in self.running_audits.keys()
        }
    
    async def stop_all_agents(self):
        """Stop all running agents."""
        for agent in self.get_running_agents():
            agent.stop()
        
        self.logger.info("Stopped all running agents")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        total_agents = len(self.agents)
        running_agents = len(self.get_running_agents())
        total_audits = len(self.running_audits)
        running_audits = len([a for a in self.running_audits.values() if a['status'] == 'running'])
        
        # Get LLM provider stats
        llm_stats = LLMFactory.get_available_providers()
        
        return {
            'agents': {
                'total': total_agents,
                'running': running_agents,
                'idle': total_agents - running_agents
            },
            'audits': {
                'total': total_audits,
                'running': running_audits,
                'completed': len([a for a in self.running_audits.values() if a['status'] == 'completed']),
                'failed': len([a for a in self.running_audits.values() if a['status'] == 'failed'])
            },
            'llm_providers': llm_stats,
            'limits': {
                'max_concurrent_agents': self.max_concurrent_agents,
                'agent_timeout': self.agent_timeout
            }
        }
    
    def cleanup_old_audits(self, max_age_hours: int = 24):
        """Clean up old audit data."""
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        
        audits_to_remove = []
        for audit_id, audit_info in self.running_audits.items():
            if audit_info['start_time'].timestamp() < cutoff_time:
                audits_to_remove.append(audit_id)
        
        for audit_id in audits_to_remove:
            del self.running_audits[audit_id]
        
        if audits_to_remove:
            self.logger.info(f"Cleaned up {len(audits_to_remove)} old audits")
    
    def export_audit_results(self, audit_id: str, filepath: str) -> bool:
        """Export audit results to a file."""
        audit_info = self.running_audits.get(audit_id)
        if not audit_info:
            return False
        
        try:
            export_data = {
                'audit_info': {
                    'audit_id': audit_id,
                    'repository_url': audit_info['repository_url'],
                    'branch': audit_info['branch'],
                    'start_time': audit_info['start_time'].isoformat(),
                    'end_time': audit_info.get('end_time', '').isoformat() if audit_info.get('end_time') else None,
                    'status': audit_info['status'],
                    'error': audit_info.get('error')
                },
                'agent_results': {
                    agent_type: {
                        'success': result.success,
                        'data': result.data,
                        'error': result.error,
                        'metadata': result.metadata,
                        'execution_time': result.execution_time,
                        'timestamp': result.timestamp.isoformat()
                    }
                    for agent_type, result in audit_info['agent_results'].items()
                }
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export audit results: {e}")
            return False