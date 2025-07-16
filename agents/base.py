"""
Base Agent Class and Data Models

Defines the abstract base class and data structures for all AI agents
in the code auditing system.
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

from common.llm import LLMProvider, LLMRequest, LLMResponse
from common.utils import Logger, Config


class AgentStatus(Enum):
    """Agent status enumeration."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class AgentType(Enum):
    """Agent type enumeration."""
    REPOSITORY_ANALYZER = "repository_analyzer"
    ISSUE_DETECTOR = "issue_detector"
    CODE_FIXER = "code_fixer"
    TEST_RUNNER = "test_runner"
    REPORT_GENERATOR = "report_generator"
    PR_CREATOR = "pr_creator"


@dataclass
class AgentResult:
    """Result data structure for agent operations."""
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentContext:
    """Context data passed between agents."""
    audit_id: str
    repository_url: str
    branch: str
    working_directory: str
    shared_data: Dict[str, Any] = field(default_factory=dict)
    agent_results: Dict[str, AgentResult] = field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract base class for all AI agents."""
    
    def __init__(self, agent_type: AgentType, name: str = None):
        self.agent_type = agent_type
        self.name = name or agent_type.value
        self.agent_id = str(uuid.uuid4())
        self.status = AgentStatus.IDLE
        self.llm_provider: Optional[LLMProvider] = None
        self.logger = Logger().get_logger(f"agent.{self.name}")
        self.config = Config()
        self.context: Optional[AgentContext] = None
        self.result: Optional[AgentResult] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # Performance metrics
        self.llm_calls = 0
        self.total_llm_time = 0.0
        self.memory_usage = 0.0
    
    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute the agent's main logic."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and requirements."""
        pass
    
    async def run(self, context: AgentContext) -> AgentResult:
        """Run the agent with proper lifecycle management."""
        self.context = context
        self.start_time = datetime.utcnow()
        self.status = AgentStatus.RUNNING
        
        # Log agent start
        self.logger.info(
            f"Starting {self.name} agent",
            agent_id=self.agent_id,
            audit_id=context.audit_id
        )
        
        try:
            # Initialize LLM provider
            await self._initialize_llm()
            
            # Execute agent logic
            start_time = datetime.utcnow()
            self.result = await self.execute(context)
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update result with timing
            self.result.execution_time = execution_time
            self.result.timestamp = datetime.utcnow()
            
            # Update status
            if self.result.success:
                self.status = AgentStatus.COMPLETED
                self.logger.info(
                    f"{self.name} agent completed successfully",
                    agent_id=self.agent_id,
                    execution_time=execution_time
                )
            else:
                self.status = AgentStatus.FAILED
                self.logger.error(
                    f"{self.name} agent failed",
                    agent_id=self.agent_id,
                    error=self.result.error
                )
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            self.result = AgentResult(
                success=False,
                error=str(e),
                execution_time=(datetime.utcnow() - self.start_time).total_seconds()
            )
            self.logger.error(
                f"{self.name} agent failed with exception",
                agent_id=self.agent_id,
                error=str(e)
            )
        
        finally:
            self.end_time = datetime.utcnow()
            self._log_performance_metrics()
        
        return self.result
    
    async def _initialize_llm(self):
        """Initialize LLM provider."""
        from common.llm import LLMFactory
        
        # Get primary provider
        self.llm_provider = LLMFactory.get_primary_provider()
        
        if not self.llm_provider:
            raise RuntimeError("No LLM provider available")
        
        if not self.llm_provider.is_available():
            raise RuntimeError("Primary LLM provider is not available")
        
        self.logger.info(
            f"Initialized LLM provider: {self.llm_provider.provider_type.value}"
        )
    
    async def call_llm(self, request: LLMRequest) -> LLMResponse:
        """Make an LLM call with logging and metrics."""
        if not self.llm_provider:
            raise RuntimeError("LLM provider not initialized")
        
        start_time = datetime.utcnow()
        
        try:
            response = await self.llm_provider.call(request)
            
            # Update metrics
            self.llm_calls += 1
            self.total_llm_time += response.response_time
            
            # Log the call
            self.logger.info(
                "LLM call completed",
                provider=self.llm_provider.provider_type.value,
                model=response.model,
                response_time=response.response_time,
                tokens_used=response.usage.get('total_tokens', 0) if response.usage else 0
            )
            
            return response
            
        except Exception as e:
            self.logger.error(
                "LLM call failed",
                provider=self.llm_provider.provider_type.value,
                error=str(e)
            )
            raise
    
    def stop(self):
        """Stop the agent execution."""
        if self.status == AgentStatus.RUNNING:
            self.status = AgentStatus.STOPPED
            self.logger.info(f"{self.name} agent stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'type': self.agent_type.value,
            'status': self.status.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'execution_time': self.result.execution_time if self.result else None,
            'llm_calls': self.llm_calls,
            'total_llm_time': self.total_llm_time,
            'memory_usage': self.memory_usage
        }
    
    def _log_performance_metrics(self):
        """Log performance metrics."""
        if self.result:
            self.logger.info(
                "Agent performance metrics",
                agent_name=self.name,
                agent_id=self.agent_id,
                execution_time=self.result.execution_time,
                llm_calls=self.llm_calls,
                total_llm_time=self.total_llm_time,
                success=self.result.success
            )
    
    def save_result(self, filepath: str):
        """Save agent result to file."""
        if self.result:
            result_data = {
                'agent_id': self.agent_id,
                'agent_name': self.name,
                'agent_type': self.agent_type.value,
                'status': self.status.value,
                'result': {
                    'success': self.result.success,
                    'data': self.result.data,
                    'error': self.result.error,
                    'metadata': self.result.metadata,
                    'execution_time': self.result.execution_time,
                    'timestamp': self.result.timestamp.isoformat()
                },
                'performance': {
                    'llm_calls': self.llm_calls,
                    'total_llm_time': self.total_llm_time,
                    'memory_usage': self.memory_usage
                }
            }
            
            try:
                with open(filepath, 'w') as f:
                    json.dump(result_data, f, indent=2, default=str)
            except Exception as e:
                self.logger.error(f"Failed to save result to {filepath}: {e}")
    
    def load_result(self, filepath: str) -> bool:
        """Load agent result from file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Validate this is the correct agent
            if data.get('agent_id') != self.agent_id:
                self.logger.warning("Result file is for different agent")
                return False
            
            # Restore result
            result_data = data['result']
            self.result = AgentResult(
                success=result_data['success'],
                data=result_data['data'],
                error=result_data.get('error'),
                metadata=result_data.get('metadata', {}),
                execution_time=result_data['execution_time'],
                timestamp=datetime.fromisoformat(result_data['timestamp'])
            )
            
            # Restore status
            self.status = AgentStatus(data['status'])
            
            # Restore performance metrics
            perf = data.get('performance', {})
            self.llm_calls = perf.get('llm_calls', 0)
            self.total_llm_time = perf.get('total_llm_time', 0.0)
            self.memory_usage = perf.get('memory_usage', 0.0)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load result from {filepath}: {e}")
            return False