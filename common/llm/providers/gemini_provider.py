#!/usr/bin/env python3
"""
Gemini Provider for AI Agent System
Integrates with Google's Gemini models
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, AsyncGenerator
import aiohttp
from .base_provider import BaseProvider
from ..exceptions import LLMError, LLMTimeoutError, LLMRateLimitError, LLMAuthenticationError


class GeminiProvider(BaseProvider):
    """Google Gemini provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Gemini provider"""
        super().__init__(config)
        self.base_url = config.get("base_url", "https://generativelanguage.googleapis.com/v1beta")
        self.default_model = config.get("model", "gemini-pro")
        self.max_tokens = config.get("max_tokens", 4000)
        self.temperature = config.get("temperature", 0.1)
        
        self.available_models = [
            "gemini-pro",
            "gemini-pro-vision",
            "gemini-ultra"
        ]
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate text using Gemini API"""
        await self._rate_limit_check()
        
        model_name = model or self.default_model
        params = self._prepare_request_params(**kwargs)
        
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "maxOutputTokens": params.get("max_tokens", self.max_tokens),
                "temperature": params.get("temperature", self.temperature),
                "topP": params.get("top_p", 0.95),
            }
        }
        
        return await self._retry_with_backoff(self._make_request, model_name, data)
    
    async def _make_request(self, model_name: str, data: Dict[str, Any]) -> str:
        """Make request to Gemini API"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/models/{model_name}:generateContent"
            headers = {
                "Content-Type": "application/json"
            }
            params = {"key": self.api_key}
            
            try:
                async with session.post(
                    url,
                    json=data,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['candidates'][0]['content']['parts'][0]['text']
                    else:
                        await self._handle_error_response(response)
            
            except asyncio.TimeoutError:
                raise LLMTimeoutError("Request to Gemini API timed out")
            except aiohttp.ClientError as e:
                raise LLMError(f"Network error: {e}")
    
    async def _handle_error_response(self, response: aiohttp.ClientResponse) -> None:
        """Handle error responses from API"""
        try:
            error_data = await response.json()
            error_message = error_data.get('error', {}).get('message', 'Unknown error')
            error_code = error_data.get('error', {}).get('code')
        except:
            error_message = f"HTTP {response.status}"
            error_code = str(response.status)
        
        if response.status == 401:
            raise LLMAuthenticationError(error_message, provider="gemini", error_code=error_code)
        elif response.status == 429:
            raise LLMRateLimitError(error_message, provider="gemini")
        else:
            raise LLMError(error_message, provider="gemini", error_code=error_code)