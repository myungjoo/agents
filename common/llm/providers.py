"""
Concrete LLM Provider Implementations

Implements specific providers for OpenAI, Google Gemini, Anthropic Claude,
and custom LLM services.
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional
import openai
import google.generativeai as genai
import anthropic

from .base import LLMProvider, LLMResponse, LLMRequest, LLMProviderType


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.client = openai.AsyncOpenAI(api_key=self.api_key)
    
    def _get_provider_type(self) -> LLMProviderType:
        return LLMProviderType.OPENAI
    
    def _get_default_model(self) -> str:
        return "gpt-4"
    
    def _validate_config(self) -> bool:
        return bool(self.api_key and self.api_key != "your-openai-api-key")
    
    async def _call_api(self, request: LLMRequest) -> LLMResponse:
        """Make API call to OpenAI."""
        messages = []
        
        if request.system_message:
            messages.append({"role": "system", "content": request.system_message})
        
        messages.append({"role": "user", "content": request.prompt})
        
        response = await self.client.chat.completions.create(
            model=request.model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            },
            finish_reason=response.choices[0].finish_reason
        )


class GeminiProvider(LLMProvider):
    """Google Gemini provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model)
    
    def _get_provider_type(self) -> LLMProviderType:
        return LLMProviderType.GEMINI
    
    def _get_default_model(self) -> str:
        return "gemini-pro"
    
    def _validate_config(self) -> bool:
        return bool(self.api_key and self.api_key != "your-gemini-api-key")
    
    async def _call_api(self, request: LLMRequest) -> LLMResponse:
        """Make API call to Google Gemini."""
        # Create a new model instance for each request to handle different parameters
        model = genai.GenerativeModel(request.model)
        
        # Prepare the prompt
        if request.system_message:
            full_prompt = f"{request.system_message}\n\n{request.prompt}"
        else:
            full_prompt = request.prompt
        
        # Generate content
        response = await asyncio.to_thread(
            model.generate_content,
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=request.temperature,
                max_output_tokens=request.max_tokens
            )
        )
        
        return LLMResponse(
            content=response.text,
            model=request.model,
            finish_reason="stop" if response.candidates[0].finish_reason == 1 else "length"
        )


class ClaudeProvider(LLMProvider):
    """Anthropic Claude provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
    
    def _get_provider_type(self) -> LLMProviderType:
        return LLMProviderType.CLAUDE
    
    def _get_default_model(self) -> str:
        return "claude-3-sonnet-20240229"
    
    def _validate_config(self) -> bool:
        return bool(self.api_key and self.api_key != "your-claude-api-key")
    
    async def _call_api(self, request: LLMRequest) -> LLMResponse:
        """Make API call to Anthropic Claude."""
        messages = []
        
        if request.system_message:
            messages.append({"role": "system", "content": request.system_message})
        
        messages.append({"role": "user", "content": request.prompt})
        
        response = await self.client.messages.create(
            model=request.model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            usage={
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens
            },
            finish_reason=response.stop_reason
        )


class CustomProvider(LLMProvider):
    """Custom LLM provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.endpoint = config.get('endpoint')
        self.api_key = config.get('api_key')
        self.headers = config.get('headers', {})
        self.request_format = config.get('request_format', 'openai')
    
    def _get_provider_type(self) -> LLMProviderType:
        return LLMProviderType.CUSTOM
    
    def _get_default_model(self) -> str:
        return "custom-model"
    
    def _validate_config(self) -> bool:
        return bool(self.endpoint and self.api_key)
    
    async def _call_api(self, request: LLMRequest) -> LLMResponse:
        """Make API call to custom LLM service."""
        async with aiohttp.ClientSession() as session:
            payload = self._format_request(request)
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                **self.headers
            }
            
            async with session.post(
                self.endpoint,
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    raise Exception(f"API call failed with status {response.status}")
                
                data = await response.json()
                return self._parse_response(data, request.model)
    
    def _format_request(self, request: LLMRequest) -> Dict[str, Any]:
        """Format request according to the specified format."""
        if self.request_format == 'openai':
            messages = []
            if request.system_message:
                messages.append({"role": "system", "content": request.system_message})
            messages.append({"role": "user", "content": request.prompt})
            
            return {
                "model": request.model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens
            }
        elif self.request_format == 'anthropic':
            messages = []
            if request.system_message:
                messages.append({"role": "system", "content": request.system_message})
            messages.append({"role": "user", "content": request.prompt})
            
            return {
                "model": request.model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens
            }
        else:
            # Generic format
            return {
                "prompt": request.prompt,
                "system_message": request.system_message,
                "model": request.model,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens
            }
    
    def _parse_response(self, data: Dict[str, Any], model: str) -> LLMResponse:
        """Parse response from custom LLM service."""
        # Try to extract content from common response formats
        content = None
        
        if 'choices' in data and len(data['choices']) > 0:
            choice = data['choices'][0]
            if 'message' in choice:
                content = choice['message'].get('content', '')
            elif 'text' in choice:
                content = choice['text']
        elif 'content' in data:
            content = data['content']
        elif 'text' in data:
            content = data['text']
        elif 'response' in data:
            content = data['response']
        
        if content is None:
            raise Exception("Could not extract content from response")
        
        return LLMResponse(
            content=content,
            model=model,
            usage=data.get('usage'),
            finish_reason=data.get('finish_reason')
        )