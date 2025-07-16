"""
Base LLM Provider Interface

Defines the abstract base class and data models for LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
import time


class LLMProviderType(Enum):
    """Supported LLM provider types."""
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"
    CUSTOM = "custom"


@dataclass
class LLMRequest:
    """Request model for LLM calls."""
    prompt: str
    system_message: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 4000
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    """Response model for LLM calls."""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    response_time: float = 0.0


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the provider with configuration."""
        self.config = config
        self.provider_type = self._get_provider_type()
        self.model = config.get('model', self._get_default_model())
        self.max_tokens = config.get('max_tokens', 4000)
        self.temperature = config.get('temperature', 0.1)
    
    @abstractmethod
    def _get_provider_type(self) -> LLMProviderType:
        """Return the provider type."""
        pass
    
    @abstractmethod
    def _get_default_model(self) -> str:
        """Return the default model for this provider."""
        pass
    
    @abstractmethod
    async def _call_api(self, request: LLMRequest) -> LLMResponse:
        """Make the actual API call to the LLM service."""
        pass
    
    async def call(self, request: LLMRequest) -> LLMResponse:
        """Make an LLM call with error handling and timing."""
        start_time = time.time()
        
        try:
            # Merge request parameters with provider defaults
            merged_request = self._merge_request(request)
            
            # Make the API call
            response = await self._call_api(merged_request)
            
            # Add timing information
            response.response_time = time.time() - start_time
            
            return response
            
        except Exception as e:
            # Return error response
            return LLMResponse(
                content="",
                model=self.model,
                error=str(e),
                response_time=time.time() - start_time
            )
    
    def _merge_request(self, request: LLMRequest) -> LLMRequest:
        """Merge request parameters with provider defaults."""
        return LLMRequest(
            prompt=request.prompt,
            system_message=request.system_message,
            temperature=request.temperature or self.temperature,
            max_tokens=request.max_tokens or self.max_tokens,
            model=request.model or self.model,
            metadata=request.metadata
        )
    
    async def call_batch(self, requests: List[LLMRequest]) -> List[LLMResponse]:
        """Make multiple LLM calls concurrently."""
        tasks = [self.call(req) for req in requests]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def is_available(self) -> bool:
        """Check if the provider is available and configured."""
        return self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> bool:
        """Validate the provider configuration."""
        pass
    
    def get_usage_info(self) -> Dict[str, Any]:
        """Get usage information for the provider."""
        return {
            'provider_type': self.provider_type.value,
            'model': self.model,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }