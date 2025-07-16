"""
LLM Configuration Management

Handles configuration for LLM providers including API keys,
model settings, fallback preferences, and cost limits.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import os
import json


class ProviderConfig(BaseModel):
    """Configuration for a single LLM provider."""
    name: str = Field(..., description="Provider name")
    enabled: bool = Field(True, description="Whether this provider is enabled")
    api_key: str = Field(..., description="API key for the provider")
    base_url: Optional[str] = Field(None, description="Custom base URL")
    default_model: str = Field(..., description="Default model to use")
    models: List[str] = Field(default_factory=list, description="Available models")
    max_tokens: int = Field(4096, description="Maximum tokens per request")
    rate_limit: int = Field(60, description="Rate limit per minute")
    priority: int = Field(1, description="Provider priority (1=highest)")
    cost_limit_per_day: Optional[float] = Field(None, description="Daily cost limit in USD")
    timeout: int = Field(30, description="Request timeout in seconds")
    retry_attempts: int = Field(3, description="Number of retry attempts")
    
    class Config:
        extra = "allow"


class LLMConfig(BaseModel):
    """Main LLM configuration."""
    providers: Dict[str, ProviderConfig] = Field(default_factory=dict)
    fallback_order: List[str] = Field(default_factory=list, description="Provider fallback order")
    load_balancing: bool = Field(True, description="Enable load balancing")
    cost_tracking: bool = Field(True, description="Enable cost tracking")
    max_concurrent_requests: int = Field(10, description="Maximum concurrent requests")
    default_temperature: float = Field(0.7, description="Default temperature")
    default_max_tokens: int = Field(4096, description="Default max tokens")
    logging_level: str = Field("INFO", description="Logging level")
    
    @classmethod
    def load_from_env(cls) -> "LLMConfig":
        """Load configuration from environment variables."""
        config = cls()
        
        # OpenAI configuration
        if openai_key := os.getenv("OPENAI_API_KEY"):
            config.providers["openai"] = ProviderConfig(
                name="openai",
                api_key=openai_key,
                base_url=os.getenv("OPENAI_BASE_URL"),
                default_model=os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4"),
                models=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                priority=1
            )
        
        # Gemini configuration
        if gemini_key := os.getenv("GEMINI_API_KEY"):
            config.providers["gemini"] = ProviderConfig(
                name="gemini",
                api_key=gemini_key,
                default_model=os.getenv("GEMINI_DEFAULT_MODEL", "gemini-pro"),
                models=["gemini-pro", "gemini-pro-vision"],
                priority=2
            )
        
        # Claude configuration
        if claude_key := os.getenv("ANTHROPIC_API_KEY"):
            config.providers["claude"] = ProviderConfig(
                name="claude",
                api_key=claude_key,
                default_model=os.getenv("CLAUDE_DEFAULT_MODEL", "claude-3-sonnet-20240229"),
                models=["claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
                priority=3
            )
        
        # Set fallback order based on priority
        config.fallback_order = sorted(
            config.providers.keys(),
            key=lambda p: config.providers[p].priority
        )
        
        return config
    
    @classmethod
    def load_from_file(cls, file_path: str) -> "LLMConfig":
        """Load configuration from JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        config = cls(**data)
        
        # Convert provider dictionaries to ProviderConfig objects
        for name, provider_data in config.providers.items():
            if isinstance(provider_data, dict):
                config.providers[name] = ProviderConfig(**provider_data)
        
        return config
    
    def save_to_file(self, file_path: str) -> None:
        """Save configuration to JSON file."""
        data = self.dict()
        
        # Convert ProviderConfig objects to dictionaries
        for name, provider in data["providers"].items():
            if hasattr(provider, 'dict'):
                data["providers"][name] = provider.dict()
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_enabled_providers(self) -> Dict[str, ProviderConfig]:
        """Get all enabled providers."""
        return {name: config for name, config in self.providers.items() if config.enabled}
    
    def get_provider_by_priority(self) -> List[str]:
        """Get providers ordered by priority."""
        enabled = self.get_enabled_providers()
        return sorted(enabled.keys(), key=lambda p: enabled[p].priority)
    
    def add_provider(self, provider_config: ProviderConfig) -> None:
        """Add a new provider configuration."""
        self.providers[provider_config.name] = provider_config
        if provider_config.name not in self.fallback_order:
            self.fallback_order.append(provider_config.name)
    
    def remove_provider(self, provider_name: str) -> None:
        """Remove a provider configuration."""
        if provider_name in self.providers:
            del self.providers[provider_name]
        if provider_name in self.fallback_order:
            self.fallback_order.remove(provider_name)
    
    def update_provider(self, provider_name: str, updates: Dict[str, Any]) -> None:
        """Update provider configuration."""
        if provider_name in self.providers:
            provider = self.providers[provider_name]
            for key, value in updates.items():
                if hasattr(provider, key):
                    setattr(provider, key, value)