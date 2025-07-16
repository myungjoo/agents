#!/usr/bin/env python3
"""
Base LLM Provider class for AI Agent System
Defines interface for all LLM providers
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator
import asyncio
import time


class BaseProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize provider
        
        Args:
            config: Provider-specific configuration
        """
        self.config = config
        self.api_key = config.get("api_key")
        self.model = config.get("model")
        self.base_url = config.get("base_url")
        self.timeout = config.get("timeout", 60)
        self.max_retries = config.get("max_retries", 3)
        self.retry_delay = config.get("retry_delay", 1)
        
        # Rate limiting
        self.rate_limit = config.get("rate_limit", 60)  # requests per minute
        self._request_times: List[float] = []
        
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate text response
        
        Args:
            prompt: Input prompt
            model: Model name (optional)
            **kwargs: Provider-specific parameters
            
        Returns:
            Generated text
        """
        pass
    
    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate structured response (JSON)
        
        Args:
            prompt: Input prompt
            schema: JSON schema for response structure
            model: Model name (optional)
            **kwargs: Provider-specific parameters
            
        Returns:
            Structured response as dictionary
        """
        # Default implementation - providers can override
        response = await self.generate(prompt, model=model, **kwargs)
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse JSON response: {response}")
    
    async def stream_generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming text response
        
        Args:
            prompt: Input prompt
            model: Model name (optional)
            **kwargs: Provider-specific parameters
            
        Yields:
            Text chunks
        """
        # Default implementation - generate full response and yield it
        response = await self.generate(prompt, model=model, **kwargs)
        yield response
    
    async def health_check(self) -> bool:
        """
        Check if provider is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            await self.generate("Hello", max_tokens=1)
            return True
        except Exception:
            return False
    
    async def _rate_limit_check(self) -> None:
        """Check and enforce rate limits"""
        current_time = time.time()
        
        # Remove requests older than 1 minute
        self._request_times = [
            t for t in self._request_times 
            if current_time - t < 60
        ]
        
        # Check if we're within rate limit
        if len(self._request_times) >= self.rate_limit:
            sleep_time = 60 - (current_time - self._request_times[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        # Record this request
        self._request_times.append(current_time)
    
    async def _retry_with_backoff(self, func, *args, **kwargs):
        """Retry function with exponential backoff"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                else:
                    break
        
        raise last_exception
    
    def _prepare_request_params(self, **kwargs) -> Dict[str, Any]:
        """Prepare common request parameters"""
        params = {}
        
        # Common parameters
        if "max_tokens" in kwargs:
            params["max_tokens"] = kwargs["max_tokens"]
        if "temperature" in kwargs:
            params["temperature"] = kwargs["temperature"]
        if "top_p" in kwargs:
            params["top_p"] = kwargs["top_p"]
        if "frequency_penalty" in kwargs:
            params["frequency_penalty"] = kwargs["frequency_penalty"]
        if "presence_penalty" in kwargs:
            params["presence_penalty"] = kwargs["presence_penalty"]
        
        return params
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model})"