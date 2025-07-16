#!/usr/bin/env python3
"""
Agent Runner for AI Agent System
Runs agents as standalone processes
"""

import asyncio
import argparse
import signal
import sys
from pathlib import Path
from typing import Dict, Any

from common.config import ConfigManager
from common.llm import LLMManager
from common.utils.logging import setup_logging, get_agent_logger
from .repo_analyzer.agent import RepoAnalyzerAgent
from .issue_finder.agent import IssueFinderAgent
from .code_tester.agent import CodeTesterAgent
from .report_generator.agent import ReportGeneratorAgent


logger = get_agent_logger("agent_runner")


class AgentRunner:
    """Runs individual agents as standalone processes"""
    
    def __init__(self, config_path: str):
        """
        Initialize agent runner
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = None
        self.llm_manager = None
        self.agent = None
        self.running = False
        
        # Available agents
        self.agent_classes = {
            "repo_analyzer": RepoAnalyzerAgent,
            "issue_finder": IssueFinderAgent,
            "code_tester": CodeTesterAgent,
            "report_generator": ReportGeneratorAgent
        }
    
    async def initialize(self, agent_type: str) -> None:
        """
        Initialize the runner with specified agent type
        
        Args:
            agent_type: Type of agent to run
        """
        # Load configuration
        self.config = ConfigManager(self.config_path)
        
        # Setup logging
        log_config = self.config.get_section("logging")
        setup_logging(
            level=log_config.get("level", "INFO"),
            format_type=log_config.get("format", "structured"),
            log_file=log_config.get("file"),
            max_size=log_config.get("max_size", "100MB"),
            backup_count=log_config.get("backup_count", 5)
        )
        
        # Initialize LLM manager
        llm_config = self.config.get_section("llm")
        self.llm_manager = LLMManager(llm_config)
        
        # Create agent instance
        if agent_type not in self.agent_classes:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        agent_class = self.agent_classes[agent_type]
        self.agent = agent_class(
            agent_id=f"{agent_type}_1", 
            config=self.config,
            llm_manager=self.llm_manager
        )
        
        logger.info(f"Initialized {agent_type} agent")
    
    async def run(self) -> None:
        """Run the agent"""
        if not self.agent:
            raise RuntimeError("Agent not initialized")
        
        self.running = True
        
        # Setup signal handlers
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start agent
        await self.agent.start()
        
        logger.info("Agent runner started, waiting for tasks...")
        
        try:
            while self.running:
                # Check for health
                if not await self.agent.health_check():
                    logger.warning("Agent health check failed")
                
                # In a real implementation, this would:
                # 1. Listen for tasks from the task queue/MCP
                # 2. Execute tasks as they arrive
                # 3. Report results back
                
                # For now, just sleep and maintain the agent
                await asyncio.sleep(10)
                
        except Exception as e:
            logger.error(f"Agent runner error: {e}")
        finally:
            await self.agent.stop()
            logger.info("Agent runner stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get runner status"""
        if not self.agent:
            return {"status": "not_initialized"}
        
        return {
            "runner_status": "running" if self.running else "stopped",
            "agent_status": self.agent.get_status(),
            "agent_metrics": self.agent.get_metrics()
        }


async def main():
    """Main entry point for agent runner"""
    parser = argparse.ArgumentParser(description="AI Agent Runner")
    parser.add_argument(
        "--agent", 
        required=True,
        choices=["repo_analyzer", "issue_finder", "code_tester", "report_generator"],
        help="Type of agent to run"
    )
    parser.add_argument(
        "--config", 
        default="config/config.yaml",
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    try:
        runner = AgentRunner(args.config)
        await runner.initialize(args.agent)
        await runner.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())