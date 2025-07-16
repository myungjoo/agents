#!/usr/bin/env python3
"""
OpenAI Provider for AI Agent System
Integrates with ChatGPT and other OpenAI models
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, AsyncGenerator
import aiohttp
from .base_provider import BaseProvider
from ..exceptions import LLMError, LLMTimeoutError, LLMRateLimitError, LLMAuthenticationError


class OpenAIProvider(BaseProvider):
    """OpenAI ChatGPT provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenAI provider"""
        super().__init__(config)
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self.default_model = config.get("model", "gpt-4-turbo-preview")
        self.max_tokens = config.get("max_tokens", 4000)
        self.temperature = config.get("temperature", 0.1)
        
        self.available_models = [
            "gpt-4-turbo-preview",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate text using OpenAI API"""
        await self._rate_limit_check()
        
        model_name = model or self.default_model
        
        # Prepare request parameters
        params = self._prepare_request_params(**kwargs)
        
        messages = [{"role": "user", "content": prompt}]
        
        data = {
            "model": model_name,
            "messages": messages,
            "max_tokens": params.get("max_tokens", self.max_tokens),
            "temperature": params.get("temperature", self.temperature),
            **{k: v for k, v in params.items() if k not in ["max_tokens", "temperature"]}
        }
        
        return await self._retry_with_backoff(self._make_request, data)
    
    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate structured JSON response"""
        # Add JSON format instruction to prompt
        json_prompt = f"{prompt}\n\nRespond with valid JSON that matches this schema:\n{json.dumps(schema, indent=2)}"
        
        response = await self.generate(json_prompt, model=model, **kwargs)
        
        # Try to parse JSON
        try:
            # Clean response - remove markdown formatting if present
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            
            return json.loads(cleaned_response.strip())
        except json.JSONDecodeError as e:
            raise LLMError(f"Failed to parse JSON response: {e}")
    
    async def stream_generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming text response"""
        await self._rate_limit_check()
        
        model_name = model or self.default_model
        params = self._prepare_request_params(**kwargs)
        
        messages = [{"role": "user", "content": prompt}]
        
        data = {
            "model": model_name,
            "messages": messages,
            "max_tokens": params.get("max_tokens", self.max_tokens),
            "temperature": params.get("temperature", self.temperature),
            "stream": True,
            **{k: v for k, v in params.items() if k not in ["max_tokens", "temperature"]}
        }
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status != 200:
                    await self._handle_error_response(response)
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data_part = line[6:]
                        if data_part == '[DONE]':
                            break
                        
                        try:
                            chunk_data = json.loads(data_part)
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                delta = chunk_data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    yield delta['content']
                        except json.JSONDecodeError:
                            continue
    
    async def _make_request(self, data: Dict[str, Any]) -> str:
        """Make request to OpenAI API"""
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            try:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content']
                    else:
                        await self._handle_error_response(response)
            
            except asyncio.TimeoutError:
                raise LLMTimeoutError("Request to OpenAI API timed out")
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
            raise LLMAuthenticationError(error_message, provider="openai", error_code=error_code)
        elif response.status == 429:
            retry_after = response.headers.get('Retry-After')
            raise LLMRateLimitError(error_message, provider="openai", retry_after=retry_after)
        else:
            raise LLMError(error_message, provider="openai", error_code=error_code)
    
    async def health_check(self) -> bool:
        """Check OpenAI API health"""
        try:
            await self.generate("Hello", max_tokens=1)
            return True
        except Exception:
            return False