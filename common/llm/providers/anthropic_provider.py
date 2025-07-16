#!/usr/bin/env python3
"""
Anthropic Provider for AI Agent System  
Integrates with Claude models
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, AsyncGenerator
import aiohttp
from .base_provider import BaseProvider
from ..exceptions import LLMError, LLMTimeoutError, LLMRateLimitError, LLMAuthenticationError


class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Anthropic provider"""
        super().__init__(config)
        self.base_url = config.get("base_url", "https://api.anthropic.com/v1")
        self.default_model = config.get("model", "claude-3-sonnet-20240229")
        self.max_tokens = config.get("max_tokens", 4000)
        self.temperature = config.get("temperature", 0.1)
        
        self.available_models = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229", 
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0"
        ]
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate text using Anthropic API"""
        await self._rate_limit_check()
        
        model_name = model or self.default_model
        params = self._prepare_request_params(**kwargs)
        
        data = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": params.get("max_tokens", self.max_tokens),
            "temperature": params.get("temperature", self.temperature),
        }
        
        return await self._retry_with_backoff(self._make_request, data)
    
    async def _make_request(self, data: Dict[str, Any]) -> str:
        """Make request to Anthropic API"""
        async with aiohttp.ClientSession() as session:
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            try:
                async with session.post(
                    f"{self.base_url}/messages",
                    json=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['content'][0]['text']
                    else:
                        await self._handle_error_response(response)
            
            except asyncio.TimeoutError:
                raise LLMTimeoutError("Request to Anthropic API timed out")
            except aiohttp.ClientError as e:
                raise LLMError(f"Network error: {e}")
    
    async def _handle_error_response(self, response: aiohttp.ClientResponse) -> None:
        """Handle error responses from API"""
        try:
            error_data = await response.json()
            error_message = error_data.get('error', {}).get('message', 'Unknown error')
            error_type = error_data.get('error', {}).get('type')
        except:
            error_message = f"HTTP {response.status}"
            error_type = str(response.status)
        
        if response.status == 401:
            raise LLMAuthenticationError(error_message, provider="anthropic", error_code=error_type)
        elif response.status == 429:
            raise LLMRateLimitError(error_message, provider="anthropic")
        else:
            raise LLMError(error_message, provider="anthropic", error_code=error_type)