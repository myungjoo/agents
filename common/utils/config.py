"""
Configuration management for the AI Agent System.

Handles loading and managing configuration from environment variables,
configuration files, and provides validation and defaults.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from pydantic import BaseModel, Field, validator
from dataclasses import dataclass


class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: str = Field(..., description="Database URL")
    pool_size: int = Field(10, description="Connection pool size")
    max_overflow: int = Field(20, description="Maximum overflow connections")
    pool_timeout: int = Field(30, description="Pool timeout in seconds")
    echo: bool = Field(False, description="Echo SQL queries")


class RedisConfig(BaseModel):
    """Redis configuration."""
    url: str = Field("redis://localhost:6379", description="Redis URL")
    max_connections: int = Field(20, description="Maximum connections")
    decode_responses: bool = Field(True, description="Decode responses")


class WebConfig(BaseModel):
    """Web interface configuration."""
    host: str = Field("0.0.0.0", description="Host to bind to")
    port: int = Field(8080, description="Port to bind to")
    debug: bool = Field(False, description="Debug mode")
    secret_key: str = Field(..., description="Secret key for sessions")
    cors_origins: List[str] = Field(default_factory=list, description="CORS origins")


class ConsoleConfig(BaseModel):
    """Console interface configuration."""
    socket_path: str = Field("/tmp/ai_agents.sock", description="Unix socket path")
    auth_required: bool = Field(True, description="Whether authentication is required")
    timeout: int = Field(30, description="Command timeout in seconds")


class GitConfig(BaseModel):
    """Git configuration."""
    username: str = Field(..., description="Git username")
    email: str = Field(..., description="Git email")
    token: Optional[str] = Field(None, description="Git token for authentication")


class AgentConfig(BaseModel):
    """Individual agent configuration."""
    enabled: bool = Field(True, description="Whether agent is enabled")
    max_concurrent_tasks: int = Field(3, description="Maximum concurrent tasks")
    timeout: int = Field(1800, description="Task timeout in seconds")  # 30 minutes
    retry_attempts: int = Field(3, description="Number of retry attempts")
    resource_limits: Dict[str, Any] = Field(default_factory=dict, description="Resource limits")


class MCPConfig(BaseModel):
    """MCP (Model Context Protocol) configuration."""
    enabled: bool = Field(True, description="Whether MCP is enabled")
    port: int = Field(8081, description="MCP server port")
    allowed_clients: List[str] = Field(default_factory=list, description="Allowed client IPs")
    max_connections: int = Field(100, description="Maximum connections")


class A2AConfig(BaseModel):
    """Agent-to-Agent communication configuration."""
    enabled: bool = Field(True, description="Whether A2A is enabled")
    port: int = Field(8082, description="A2A communication port")
    encryption_key: Optional[str] = Field(None, description="Encryption key for A2A messages")
    max_message_size: int = Field(1024 * 1024, description="Maximum message size in bytes")


class Config(BaseModel):
    """Main configuration class."""
    # Core settings
    debug: bool = Field(False, description="Debug mode")
    log_level: str = Field("INFO", description="Logging level")
    data_dir: str = Field("./data", description="Data directory")
    temp_dir: str = Field("./temp", description="Temporary directory")
    
    # Service configurations
    database: DatabaseConfig = Field(..., description="Database configuration")
    redis: RedisConfig = Field(default_factory=RedisConfig, description="Redis configuration")
    web: WebConfig = Field(..., description="Web interface configuration")
    console: ConsoleConfig = Field(default_factory=ConsoleConfig, description="Console configuration")
    
    # External service configurations
    git: GitConfig = Field(..., description="Git configuration")
    mcp: MCPConfig = Field(default_factory=MCPConfig, description="MCP configuration")
    a2a: A2AConfig = Field(default_factory=A2AConfig, description="A2A configuration")
    
    # Agent configurations
    agents: Dict[str, AgentConfig] = Field(default_factory=dict, description="Agent configurations")
    
    # System limits
    max_repository_size: int = Field(1024 * 1024 * 1024, description="Max repository size in bytes")  # 1GB
    max_analysis_time: int = Field(3600, description="Max analysis time in seconds")  # 1 hour
    max_concurrent_audits: int = Field(5, description="Maximum concurrent audits")
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()
    
    @classmethod
    def load_from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        # Database configuration
        database_config = DatabaseConfig(
            url=os.getenv("DATABASE_URL", "sqlite:///./data/ai_agents.db"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
            echo=os.getenv("DB_ECHO", "false").lower() == "true"
        )
        
        # Web configuration
        web_config = WebConfig(
            host=os.getenv("WEB_HOST", "0.0.0.0"),
            port=int(os.getenv("WEB_PORT", "8080")),
            debug=os.getenv("WEB_DEBUG", "false").lower() == "true",
            secret_key=os.getenv("WEB_SECRET_KEY", os.urandom(32).hex()),
            cors_origins=os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []
        )
        
        # Git configuration
        git_config = GitConfig(
            username=os.getenv("GIT_USERNAME", "ai-agent"),
            email=os.getenv("GIT_EMAIL", "ai-agent@example.com"),
            token=os.getenv("GIT_TOKEN")
        )
        
        # Redis configuration
        redis_config = RedisConfig(
            url=os.getenv("REDIS_URL", "redis://localhost:6379"),
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "20"))
        )
        
        # Load agent configurations
        agents_config = {}
        agent_names = [
            "repository_analyzer", "issue_detector", "code_fixer", 
            "test_runner", "report_generator", "pr_creator"
        ]
        
        for agent_name in agent_names:
            prefix = f"{agent_name.upper()}_"
            agents_config[agent_name] = AgentConfig(
                enabled=os.getenv(f"{prefix}ENABLED", "true").lower() == "true",
                max_concurrent_tasks=int(os.getenv(f"{prefix}MAX_TASKS", "3")),
                timeout=int(os.getenv(f"{prefix}TIMEOUT", "1800")),
                retry_attempts=int(os.getenv(f"{prefix}RETRY_ATTEMPTS", "3"))
            )
        
        return cls(
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            data_dir=os.getenv("DATA_DIR", "./data"),
            temp_dir=os.getenv("TEMP_DIR", "./temp"),
            database=database_config,
            redis=redis_config,
            web=web_config,
            git=git_config,
            agents=agents_config,
            max_repository_size=int(os.getenv("MAX_REPOSITORY_SIZE", str(1024 * 1024 * 1024))),
            max_analysis_time=int(os.getenv("MAX_ANALYSIS_TIME", "3600")),
            max_concurrent_audits=int(os.getenv("MAX_CONCURRENT_AUDITS", "5"))
        )
    
    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> "Config":
        """Load configuration from file (JSON or YAML)."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        return cls(**data)
    
    def save_to_file(self, file_path: Union[str, Path], format: str = "yaml"):
        """Save configuration to file."""
        file_path = Path(file_path)
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = self.dict()
        
        with open(file_path, 'w') as f:
            if format.lower() == "yaml":
                yaml.dump(data, f, default_flow_style=False, indent=2)
            else:
                json.dump(data, f, indent=2)
    
    def get_agent_config(self, agent_name: str) -> AgentConfig:
        """Get configuration for a specific agent."""
        return self.agents.get(agent_name, AgentConfig())
    
    def update_agent_config(self, agent_name: str, **kwargs):
        """Update configuration for a specific agent."""
        if agent_name not in self.agents:
            self.agents[agent_name] = AgentConfig()
        
        for key, value in kwargs.items():
            if hasattr(self.agents[agent_name], key):
                setattr(self.agents[agent_name], key, value)
    
    def get_database_url(self) -> str:
        """Get the database URL."""
        return self.database.url
    
    def get_redis_url(self) -> str:
        """Get the Redis URL."""
        return self.redis.url
    
    def ensure_directories(self):
        """Ensure required directories exist."""
        dirs_to_create = [
            self.data_dir,
            self.temp_dir,
            os.path.join(self.data_dir, "repositories"),
            os.path.join(self.data_dir, "reports"),
            os.path.join(self.data_dir, "backups"),
            "logs"
        ]
        
        for dir_path in dirs_to_create:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Check required directories are writable
        for dir_path in [self.data_dir, self.temp_dir]:
            try:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                test_file = Path(dir_path) / ".write_test"
                test_file.write_text("test")
                test_file.unlink()
            except Exception as e:
                issues.append(f"Directory {dir_path} is not writable: {e}")
        
        # Check database URL format
        if not self.database.url:
            issues.append("Database URL is required")
        
        # Check web secret key
        if len(self.web.secret_key) < 32:
            issues.append("Web secret key should be at least 32 characters")
        
        # Check Git configuration
        if not self.git.username or not self.git.email:
            issues.append("Git username and email are required")
        
        return issues
    
    def get_environment_template(self) -> str:
        """Get a template .env file with all possible configuration options."""
        template = """# AI Agent System Configuration

# Core Settings
DEBUG=false
LOG_LEVEL=INFO
DATA_DIR=./data
TEMP_DIR=./temp

# Database Configuration
DATABASE_URL=sqlite:///./data/ai_agents.db
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_ECHO=false

# Redis Configuration  
REDIS_URL=redis://localhost:6379
REDIS_MAX_CONNECTIONS=20

# Web Interface
WEB_HOST=0.0.0.0
WEB_PORT=8080
WEB_DEBUG=false
WEB_SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000

# Git Configuration
GIT_USERNAME=ai-agent
GIT_EMAIL=ai-agent@example.com
GIT_TOKEN=your-git-token-here

# LLM Provider API Keys
OPENAI_API_KEY=your-openai-key-here
GEMINI_API_KEY=your-gemini-key-here
ANTHROPIC_API_KEY=your-claude-key-here

# System Limits
MAX_REPOSITORY_SIZE=1073741824
MAX_ANALYSIS_TIME=3600
MAX_CONCURRENT_AUDITS=5

# Agent Configuration
REPOSITORY_ANALYZER_ENABLED=true
REPOSITORY_ANALYZER_MAX_TASKS=3
REPOSITORY_ANALYZER_TIMEOUT=1800

ISSUE_DETECTOR_ENABLED=true
ISSUE_DETECTOR_MAX_TASKS=3
ISSUE_DETECTOR_TIMEOUT=1800

CODE_FIXER_ENABLED=true
CODE_FIXER_MAX_TASKS=3
CODE_FIXER_TIMEOUT=1800

TEST_RUNNER_ENABLED=true
TEST_RUNNER_MAX_TASKS=2
TEST_RUNNER_TIMEOUT=1800

REPORT_GENERATOR_ENABLED=true
REPORT_GENERATOR_MAX_TASKS=2
REPORT_GENERATOR_TIMEOUT=900

PR_CREATOR_ENABLED=true
PR_CREATOR_MAX_TASKS=1
PR_CREATOR_TIMEOUT=600
"""
        return template