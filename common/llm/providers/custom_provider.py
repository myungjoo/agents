#!/usr/bin/env python3
"""
Custom Provider for AI Agent System
Generic implementation for custom LLM endpoints
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, AsyncGenerator
import aiohttp
from .base_provider import BaseProvider
from ..exceptions import LLMError, LLMTimeoutError, LLMRateLimitError, LLMAuthenticationError


class CustomProvider(BaseProvider):
    """Custom LLM provider for generic endpoints"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize custom provider"""
        super().__init__(config)
        self.base_url = config.get("base_url")
        self.default_model = config.get("model", "custom-model")
        self.max_tokens = config.get("max_tokens", 4000)
        self.temperature = config.get("temperature", 0.1)
        self.auth_header = config.get("auth_header", "Authorization")
        self.auth_prefix = config.get("auth_prefix", "Bearer")
        self.endpoint = config.get("endpoint", "/v1/chat/completions")
        
        if not self.base_url:
            raise ValueError("base_url is required for custom provider")
        
        self.available_models = config.get("available_models", [self.default_model])
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate text using custom API"""
        await self._rate_limit_check()
        
        model_name = model or self.default_model
        params = self._prepare_request_params(**kwargs)
        
        # Try OpenAI-compatible format first
        data = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": params.get("max_tokens", self.max_tokens),
            "temperature": params.get("temperature", self.temperature),
            **{k: v for k, v in params.items() if k not in ["max_tokens", "temperature"]}
        }
        
        return await self._retry_with_backoff(self._make_request, data)
    
    async def _make_request(self, data: Dict[str, Any]) -> str:
        """Make request to custom API"""
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json"
            }
            
            # Add authentication header
            if self.api_key:
                headers[self.auth_header] = f"{self.auth_prefix} {self.api_key}"
            
            try:
                url = f"{self.base_url.rstrip('/')}{self.endpoint}"
                async with session.post(
                    url,
                    json=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Try OpenAI format
                        if 'choices' in result and len(result['choices']) > 0:
                            return result['choices'][0]['message']['content']
                        
                        # Try simple text format
                        if 'text' in result:
                            return result['text']
                        
                        # Try response format
                        if 'response' in result:
                            return result['response']
                        
                        # If no standard format, return the whole response as string
                        return str(result)
                    else:
                        await self._handle_error_response(response)
            
            except asyncio.TimeoutError:
                raise LLMTimeoutError("Request to custom API timed out")
            except aiohttp.ClientError as e:
                raise LLMError(f"Network error: {e}")
    
    async def _handle_error_response(self, response: aiohttp.ClientResponse) -> None:
        """Handle error responses from API"""
        try:
            error_data = await response.json()
            if 'error' in error_data:
                error_info = error_data['error']
                if isinstance(error_info, dict):
                    error_message = error_info.get('message', 'Unknown error')
                    error_code = error_info.get('code')
                else:
                    error_message = str(error_info)
                    error_code = None
            else:
                error_message = str(error_data)
                error_code = None
        except:
            error_message = f"HTTP {response.status}"
            error_code = str(response.status)
        
        if response.status == 401:
            raise LLMAuthenticationError(error_message, provider="custom", error_code=error_code)
        elif response.status == 429:
            raise LLMRateLimitError(error_message, provider="custom")
        else:
            raise LLMError(error_message, provider="custom", error_code=error_code)