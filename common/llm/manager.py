#!/usr/bin/env python3
"""
LLM Manager for AI Agent System
Provides unified interface for multiple LLM providers
"""

import asyncio
from typing import Any, Dict, List, Optional, Type, Union
from .providers import OpenAIProvider, GeminiProvider, AnthropicProvider, CustomProvider
from .exceptions import LLMError, LLMModelNotFoundError
from ..utils.logging import get_agent_logger

logger = get_agent_logger("llm_manager")


class LLMManager:
    """Manages multiple LLM providers with unified interface"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LLM manager
        
        Args:
            config: LLM configuration dictionary
        """
        self.config = config
        self.providers: Dict[str, Any] = {}
        self.default_provider = config.get("default_provider", "openai")
        
        self._initialize_providers()
    
    def _initialize_providers(self) -> None:
        """Initialize all configured LLM providers"""
        provider_classes = {
            "openai": OpenAIProvider,
            "gemini": GeminiProvider,
            "anthropic": AnthropicProvider,
            "custom": CustomProvider
        }
        
        for provider_name, provider_class in provider_classes.items():
            if provider_name in self.config:
                try:
                    provider_config = self.config[provider_name]
                    self.providers[provider_name] = provider_class(provider_config)
                    logger.info(f"Initialized {provider_name} provider")
                except Exception as e:
                    logger.error(f"Failed to initialize {provider_name} provider", error=str(e))
    
    async def generate(
        self,
        prompt: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate text using specified or default provider
        
        Args:
            prompt: Input prompt
            provider: Provider name (optional, defaults to default_provider)
            model: Model name (optional, uses provider default)
            **kwargs: Additional parameters for the provider
            
        Returns:
            Generated text
        """
        provider_name = provider or self.default_provider
        
        if provider_name not in self.providers:
            raise LLMModelNotFoundError(f"Provider {provider_name} not available")
        
        provider_instance = self.providers[provider_name]
        
        try:
            logger.debug(f"Generating text with {provider_name}", model=model)
            result = await provider_instance.generate(prompt, model=model, **kwargs)
            logger.debug(f"Generated {len(result)} characters", provider=provider_name)
            return result
        except Exception as e:
            logger.error(f"Text generation failed", provider=provider_name, error=str(e))
            raise
    
    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        provider: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate structured output using JSON schema
        
        Args:
            prompt: Input prompt
            schema: JSON schema for output structure
            provider: Provider name (optional)
            **kwargs: Additional parameters
            
        Returns:
            Structured output as dictionary
        """
        provider_name = provider or self.default_provider
        
        if provider_name not in self.providers:
            raise LLMModelNotFoundError(f"Provider {provider_name} not available")
        
        provider_instance = self.providers[provider_name]
        
        if hasattr(provider_instance, 'generate_structured'):
            return await provider_instance.generate_structured(prompt, schema, **kwargs)
        else:
            # Fallback to regular generation with schema in prompt
            schema_prompt = f"{prompt}\n\nPlease respond in the following JSON format:\n{schema}"
            response = await self.generate(schema_prompt, provider=provider_name, **kwargs)
            
            # Try to parse JSON response
            import json
            try:
                return json.loads(response.strip())
            except json.JSONDecodeError:
                # Extract JSON from response if wrapped in markdown
                import re
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                raise LLMError(f"Failed to parse structured response: {response}")
    
    async def analyze_code(
        self,
        code: str,
        language: str,
        task: str = "analyze",
        provider: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze code for bugs, improvements, or other tasks
        
        Args:
            code: Source code to analyze
            language: Programming language
            task: Analysis task (analyze, review, optimize, etc.)
            provider: Provider name (optional)
            **kwargs: Additional parameters
            
        Returns:
            Analysis results
        """
        task_prompts = {
            "analyze": f"Analyze the following {language} code for potential bugs, security issues, and improvements:",
            "review": f"Perform a code review of the following {language} code:",
            "optimize": f"Suggest optimizations for the following {language} code:",
            "security": f"Analyze the following {language} code for security vulnerabilities:",
            "bugs": f"Find potential bugs in the following {language} code:",
        }
        
        prompt = f"{task_prompts.get(task, task_prompts['analyze'])}\n\n```{language}\n{code}\n```"
        
        schema = {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Brief summary of findings"},
                "issues": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "description": "Issue type"},
                            "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                            "line": {"type": "integer", "description": "Line number (if applicable)"},
                            "description": {"type": "string", "description": "Issue description"},
                            "suggestion": {"type": "string", "description": "Suggested fix"}
                        },
                        "required": ["type", "severity", "description"]
                    }
                },
                "metrics": {
                    "type": "object",
                    "properties": {
                        "complexity": {"type": "integer"},
                        "maintainability": {"type": "string", "enum": ["low", "medium", "high"]},
                        "performance": {"type": "string", "enum": ["poor", "fair", "good", "excellent"]}
                    }
                }
            },
            "required": ["summary", "issues"]
        }
        
        return await self.generate_structured(prompt, schema, provider=provider, **kwargs)
    
    async def batch_generate(
        self,
        prompts: List[str],
        provider: Optional[str] = None,
        max_concurrent: int = 5,
        **kwargs
    ) -> List[str]:
        """
        Generate text for multiple prompts concurrently
        
        Args:
            prompts: List of input prompts
            provider: Provider name (optional)
            max_concurrent: Maximum concurrent requests
            **kwargs: Additional parameters
            
        Returns:
            List of generated texts
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_single(prompt: str) -> str:
            async with semaphore:
                return await self.generate(prompt, provider=provider, **kwargs)
        
        tasks = [generate_single(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks)
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return list(self.providers.keys())
    
    def get_provider_info(self, provider: str) -> Dict[str, Any]:
        """Get information about a specific provider"""
        if provider not in self.providers:
            raise LLMModelNotFoundError(f"Provider {provider} not available")
        
        provider_instance = self.providers[provider]
        return {
            "name": provider,
            "models": getattr(provider_instance, 'available_models', []),
            "supports_streaming": hasattr(provider_instance, 'stream_generate'),
            "supports_structured": hasattr(provider_instance, 'generate_structured'),
            "default_model": getattr(provider_instance, 'default_model', None)
        }
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all providers"""
        results = {}
        
        for provider_name, provider_instance in self.providers.items():
            try:
                if hasattr(provider_instance, 'health_check'):
                    results[provider_name] = await provider_instance.health_check()
                else:
                    # Simple test generation
                    await provider_instance.generate("Hello", max_tokens=1)
                    results[provider_name] = True
            except Exception as e:
                logger.warning(f"Health check failed for {provider_name}", error=str(e))
                results[provider_name] = False
        
        return results