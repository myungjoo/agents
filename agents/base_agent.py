#!/usr/bin/env python3
"""
Base Agent class for AI Agent System
Defines interface and common functionality for all agents
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from pathlib import Path

from common.utils.logging import get_agent_logger
from common.llm import LLMManager
from common.config import ConfigManager


class AgentStatus(Enum):
    """Agent status enumeration"""
    IDLE = "idle"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    PAUSED = "paused"


@dataclass
class TaskResult:
    """Result of an agent task"""
    success: bool
    data: Any = None
    error: str = None
    metrics: Dict[str, Any] = None
    duration: float = 0.0


class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, agent_id: str, config: ConfigManager, llm_manager: LLMManager):
        """
        Initialize base agent
        
        Args:
            agent_id: Unique identifier for the agent
            config: Configuration manager
            llm_manager: LLM manager instance
        """
        self.agent_id = agent_id
        self.config = config
        self.llm_manager = llm_manager
        self.logger = get_agent_logger(f"agent_{agent_id}")
        
        # Agent state
        self.status = AgentStatus.IDLE
        self.current_task = None
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.start_time = None
        self.last_activity = None
        
        # Configuration
        self.timeout = config.get("agents.default_timeout", 3600)
        self.max_retries = config.get("agents.max_retries", 3)
        
        # Callbacks
        self.status_callbacks: List[Callable] = []
        self.task_callbacks: List[Callable] = []
        
        self.logger.info(f"Agent {agent_id} initialized")
    
    @abstractmethod
    async def process_task(self, task: Dict[str, Any]) -> TaskResult:
        """
        Process a task
        
        Args:
            task: Task configuration and data
            
        Returns:
            TaskResult with processing results
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Get list of agent capabilities
        
        Returns:
            List of capability names
        """
        pass
    
    async def start(self) -> None:
        """Start the agent"""
        if self.status != AgentStatus.STOPPED:
            self.logger.warning("Agent already running or in invalid state")
            return
        
        self.status = AgentStatus.IDLE
        self.start_time = time.time()
        self.last_activity = time.time()
        
        self.logger.info("Agent started")
        await self._notify_status_change()
    
    async def stop(self) -> None:
        """Stop the agent"""
        self.status = AgentStatus.STOPPED
        
        if self.current_task:
            self.logger.info("Stopping agent during task execution")
        
        self.logger.info("Agent stopped")
        await self._notify_status_change()
    
    async def pause(self) -> None:
        """Pause the agent"""
        if self.status == AgentStatus.RUNNING:
            self.status = AgentStatus.PAUSED
            self.logger.info("Agent paused")
            await self._notify_status_change()
    
    async def resume(self) -> None:
        """Resume the agent"""
        if self.status == AgentStatus.PAUSED:
            self.status = AgentStatus.IDLE
            self.logger.info("Agent resumed")
            await self._notify_status_change()
    
    async def execute_task(self, task: Dict[str, Any]) -> TaskResult:
        """
        Execute a task with error handling and metrics
        
        Args:
            task: Task to execute
            
        Returns:
            TaskResult with execution results
        """
        if self.status not in [AgentStatus.IDLE, AgentStatus.RUNNING]:
            return TaskResult(
                success=False,
                error=f"Agent not available (status: {self.status.value})"
            )
        
        self.current_task = task
        self.status = AgentStatus.RUNNING
        start_time = time.time()
        
        try:
            self.logger.log_task_start(task.get("type", "unknown"))
            await self._notify_status_change()
            
            # Execute with timeout
            result = await asyncio.wait_for(
                self.process_task(task),
                timeout=self.timeout
            )
            
            result.duration = time.time() - start_time
            
            if result.success:
                self.tasks_completed += 1
                self.logger.log_task_complete(
                    task.get("type", "unknown"), 
                    result.duration
                )
            else:
                self.tasks_failed += 1
                self.logger.error(
                    f"Task failed: {result.error}",
                    task_type=task.get("type", "unknown")
                )
            
            await self._notify_task_complete(task, result)
            return result
            
        except asyncio.TimeoutError:
            self.tasks_failed += 1
            error_msg = f"Task timed out after {self.timeout} seconds"
            self.logger.error(error_msg, task_type=task.get("type", "unknown"))
            
            result = TaskResult(
                success=False,
                error=error_msg,
                duration=time.time() - start_time
            )
            await self._notify_task_complete(task, result)
            return result
            
        except Exception as e:
            self.tasks_failed += 1
            error_msg = f"Task execution failed: {str(e)}"
            self.logger.log_task_error(task.get("type", "unknown"), e)
            
            result = TaskResult(
                success=False,
                error=error_msg,
                duration=time.time() - start_time
            )
            await self._notify_task_complete(task, result)
            return result
            
        finally:
            self.current_task = None
            self.status = AgentStatus.IDLE
            self.last_activity = time.time()
            await self._notify_status_change()
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status information"""
        uptime = time.time() - self.start_time if self.start_time else 0
        
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "uptime": uptime,
            "current_task": self.current_task.get("type") if self.current_task else None,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "last_activity": self.last_activity,
            "capabilities": self.get_capabilities()
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        total_tasks = self.tasks_completed + self.tasks_failed
        success_rate = self.tasks_completed / total_tasks if total_tasks > 0 else 0
        
        return {
            "total_tasks": total_tasks,
            "success_rate": success_rate,
            "uptime": time.time() - self.start_time if self.start_time else 0,
            "avg_task_duration": getattr(self, '_avg_task_duration', 0)
        }
    
    def add_status_callback(self, callback: Callable) -> None:
        """Add status change callback"""
        self.status_callbacks.append(callback)
    
    def add_task_callback(self, callback: Callable) -> None:
        """Add task completion callback"""
        self.task_callbacks.append(callback)
    
    async def _notify_status_change(self) -> None:
        """Notify status change callbacks"""
        for callback in self.status_callbacks:
            try:
                await callback(self.agent_id, self.status.value)
            except Exception as e:
                self.logger.error(f"Status callback failed: {e}")
    
    async def _notify_task_complete(self, task: Dict[str, Any], result: TaskResult) -> None:
        """Notify task completion callbacks"""
        for callback in self.task_callbacks:
            try:
                await callback(self.agent_id, task, result)
            except Exception as e:
                self.logger.error(f"Task callback failed: {e}")
    
    async def health_check(self) -> bool:
        """Perform agent health check"""
        try:
            # Check if LLM is accessible
            if self.llm_manager:
                providers = await self.llm_manager.health_check()
                if not any(providers.values()):
                    return False
            
            # Agent-specific health checks can be implemented in subclasses
            return True
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.agent_id}, status={self.status.value})"