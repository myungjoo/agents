"""
LLM Provider Implementations

Base class and specific implementations for different LLM providers
with standardized interfaces and error handling.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any, Optional, List
import aiohttp
import openai
import google.generativeai as genai
from anthropic import Anthropic

from .request import LLMRequest, LLMResponse, LLMUsage, LLMStreamChunk, LLMMessage
from ..utils import Logger


class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.logger = Logger(f"LLMProvider.{name}")
        self.is_available = False
        self._client = None
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the provider and test connectivity."""
        pass
    
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response for the given request."""
        pass
    
    @abstractmethod
    async def stream_generate(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Generate a streaming response for the given request."""
        pass
    
    @abstractmethod
    async def estimate_cost(self, request: LLMRequest) -> float:
        """Estimate the cost for the given request."""
        pass
    
    async def health_check(self) -> bool:
        """Check if the provider is healthy and available."""
        try:
            test_request = LLMRequest(
                messages=[LLMMessage(role="user", content="Hello")],
                max_tokens=1
            )
            response = await self.generate(test_request)
            return response.error is None
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("openai", config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url")
        self.default_model = config.get("default_model", "gpt-4")
        self.cost_per_token = {
            "gpt-4": {"input": 0.00003, "output": 0.00006},
            "gpt-4-turbo": {"input": 0.00001, "output": 0.00003},
            "gpt-3.5-turbo": {"input": 0.000001, "output": 0.000002}
        }
    
    async def initialize(self) -> bool:
        """Initialize OpenAI client."""
        try:
            self._client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            # Test with a simple request
            await self._client.chat.completions.create(
                model=self.default_model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1
            )
            self.is_available = True
            self.logger.info(f"OpenAI provider initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI provider: {str(e)}")
            return False
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using OpenAI API."""
        start_time = time.time()
        
        try:
            messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
            model = request.model or self.default_model
            
            response = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stream=False
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            usage = LLMUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                estimated_cost=self._calculate_cost(model, response.usage)
            )
            
            return LLMResponse(
                request_id=request.request_id,
                content=response.choices[0].message.content,
                finish_reason=response.choices[0].finish_reason,
                usage=usage,
                model=model,
                provider=self.name,
                latency_ms=latency_ms
            )
            
        except Exception as e:
            self.logger.error(f"OpenAI generation failed: {str(e)}")
            return LLMResponse(
                request_id=request.request_id,
                provider=self.name,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000
            )
    
    async def stream_generate(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Generate streaming response using OpenAI API."""
        try:
            messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
            model = request.model or self.default_model
            
            stream = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield LLMStreamChunk(
                        request_id=request.request_id,
                        content=chunk.choices[0].delta.content,
                        finish_reason=chunk.choices[0].finish_reason,
                        is_final=chunk.choices[0].finish_reason is not None
                    )
                    
        except Exception as e:
            self.logger.error(f"OpenAI streaming failed: {str(e)}")
            yield LLMStreamChunk(
                request_id=request.request_id,
                content="",
                is_final=True,
                metadata={"error": str(e)}
            )
    
    def _calculate_cost(self, model: str, usage) -> float:
        """Calculate estimated cost based on token usage."""
        rates = self.cost_per_token.get(model, self.cost_per_token["gpt-4"])
        input_cost = usage.prompt_tokens * rates["input"]
        output_cost = usage.completion_tokens * rates["output"]
        return input_cost + output_cost
    
    async def estimate_cost(self, request: LLMRequest) -> float:
        """Estimate cost for the request."""
        # Rough estimation based on average token count
        estimated_tokens = sum(len(msg.content.split()) * 1.3 for msg in request.messages)
        model = request.model or self.default_model
        rates = self.cost_per_token.get(model, self.cost_per_token["gpt-4"])
        return estimated_tokens * rates["input"] + request.max_tokens * rates["output"]


class GeminiProvider(LLMProvider):
    """Google Gemini provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("gemini", config)
        self.api_key = config.get("api_key")
        self.default_model = config.get("default_model", "gemini-pro")
        self.cost_per_token = {"input": 0.000125, "output": 0.000375}
    
    async def initialize(self) -> bool:
        """Initialize Gemini client."""
        try:
            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(self.default_model)
            
            # Test with a simple request
            await asyncio.get_event_loop().run_in_executor(
                None, self._client.generate_content, "Hello"
            )
            
            self.is_available = True
            self.logger.info("Gemini provider initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini provider: {str(e)}")
            return False
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Gemini API."""
        start_time = time.time()
        
        try:
            # Convert messages to Gemini format
            prompt = self._convert_messages_to_prompt(request.messages)
            model = genai.GenerativeModel(request.model or self.default_model)
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, model.generate_content, prompt
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Estimate token usage (Gemini doesn't provide exact counts)
            estimated_input_tokens = len(prompt.split()) * 1.3
            estimated_output_tokens = len(response.text.split()) * 1.3
            
            usage = LLMUsage(
                prompt_tokens=int(estimated_input_tokens),
                completion_tokens=int(estimated_output_tokens),
                total_tokens=int(estimated_input_tokens + estimated_output_tokens),
                estimated_cost=self._calculate_cost(estimated_input_tokens, estimated_output_tokens)
            )
            
            return LLMResponse(
                request_id=request.request_id,
                content=response.text,
                finish_reason="completed",
                usage=usage,
                model=request.model or self.default_model,
                provider=self.name,
                latency_ms=latency_ms
            )
            
        except Exception as e:
            self.logger.error(f"Gemini generation failed: {str(e)}")
            return LLMResponse(
                request_id=request.request_id,
                provider=self.name,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000
            )
    
    def _convert_messages_to_prompt(self, messages: List[LLMMessage]) -> str:
        """Convert message format to Gemini prompt."""
        prompt_parts = []
        for msg in messages:
            if msg.role == "system":
                prompt_parts.append(f"System: {msg.content}")
            elif msg.role == "user":
                prompt_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}")
        return "\n\n".join(prompt_parts)
    
    def _calculate_cost(self, input_tokens: float, output_tokens: float) -> float:
        """Calculate estimated cost."""
        return (input_tokens * self.cost_per_token["input"] + 
                output_tokens * self.cost_per_token["output"])
    
    async def stream_generate(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Gemini doesn't support streaming, so we simulate it."""
        response = await self.generate(request)
        if response.error:
            yield LLMStreamChunk(
                request_id=request.request_id,
                content="",
                is_final=True,
                metadata={"error": response.error}
            )
        else:
            # Simulate streaming by chunking the response
            words = response.content.split()
            for i in range(0, len(words), 5):
                chunk = " ".join(words[i:i+5])
                yield LLMStreamChunk(
                    request_id=request.request_id,
                    content=chunk + " ",
                    is_final=(i + 5 >= len(words))
                )
                await asyncio.sleep(0.05)  # Small delay to simulate streaming
    
    async def estimate_cost(self, request: LLMRequest) -> float:
        """Estimate cost for the request."""
        estimated_input_tokens = sum(len(msg.content.split()) * 1.3 for msg in request.messages)
        estimated_output_tokens = request.max_tokens
        return self._calculate_cost(estimated_input_tokens, estimated_output_tokens)


class ClaudeProvider(LLMProvider):
    """Anthropic Claude provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("claude", config)
        self.api_key = config.get("api_key")
        self.default_model = config.get("default_model", "claude-3-sonnet-20240229")
        self.cost_per_token = {
            "claude-3-sonnet-20240229": {"input": 0.000015, "output": 0.000075},
            "claude-3-haiku-20240307": {"input": 0.00000025, "output": 0.00000125}
        }
    
    async def initialize(self) -> bool:
        """Initialize Claude client."""
        try:
            self._client = Anthropic(api_key=self.api_key)
            
            # Test with a simple request
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._client.messages.create(
                    model=self.default_model,
                    max_tokens=1,
                    messages=[{"role": "user", "content": "Hello"}]
                )
            )
            
            self.is_available = True
            self.logger.info("Claude provider initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Claude provider: {str(e)}")
            return False
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Claude API."""
        start_time = time.time()
        
        try:
            messages = []
            system_message = ""
            
            for msg in request.messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    messages.append({"role": msg.role, "content": msg.content})
            
            kwargs = {
                "model": request.model or self.default_model,
                "max_tokens": request.max_tokens,
                "messages": messages
            }
            
            if system_message:
                kwargs["system"] = system_message
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._client.messages.create(**kwargs)
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            usage = LLMUsage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens,
                estimated_cost=self._calculate_cost(
                    request.model or self.default_model,
                    response.usage.input_tokens,
                    response.usage.output_tokens
                )
            )
            
            return LLMResponse(
                request_id=request.request_id,
                content=response.content[0].text,
                finish_reason=response.stop_reason,
                usage=usage,
                model=request.model or self.default_model,
                provider=self.name,
                latency_ms=latency_ms
            )
            
        except Exception as e:
            self.logger.error(f"Claude generation failed: {str(e)}")
            return LLMResponse(
                request_id=request.request_id,
                provider=self.name,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000
            )
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost."""
        rates = self.cost_per_token.get(model, self.cost_per_token["claude-3-sonnet-20240229"])
        return input_tokens * rates["input"] + output_tokens * rates["output"]
    
    async def stream_generate(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Claude streaming implementation."""
        try:
            messages = []
            system_message = ""
            
            for msg in request.messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    messages.append({"role": msg.role, "content": msg.content})
            
            kwargs = {
                "model": request.model or self.default_model,
                "max_tokens": request.max_tokens,
                "messages": messages,
                "stream": True
            }
            
            if system_message:
                kwargs["system"] = system_message
            
            # Claude streaming needs to be handled in executor
            def create_stream():
                return self._client.messages.create(**kwargs)
            
            stream = await asyncio.get_event_loop().run_in_executor(None, create_stream)
            
            for chunk in stream:
                if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                    yield LLMStreamChunk(
                        request_id=request.request_id,
                        content=chunk.delta.text,
                        finish_reason=getattr(chunk, 'stop_reason', None),
                        is_final=hasattr(chunk, 'stop_reason') and chunk.stop_reason is not None
                    )
                    
        except Exception as e:
            self.logger.error(f"Claude streaming failed: {str(e)}")
            yield LLMStreamChunk(
                request_id=request.request_id,
                content="",
                is_final=True,
                metadata={"error": str(e)}
            )
    
    async def estimate_cost(self, request: LLMRequest) -> float:
        """Estimate cost for the request."""
        estimated_input_tokens = sum(len(msg.content.split()) * 1.3 for msg in request.messages)
        estimated_output_tokens = request.max_tokens
        model = request.model or self.default_model
        return self._calculate_cost(model, int(estimated_input_tokens), estimated_output_tokens)