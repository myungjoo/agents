"""
LLM Manager

Central coordinator for multiple LLM providers with automatic fallback,
load balancing, cost tracking, and health monitoring.
"""

import asyncio
import random
import time
from collections import defaultdict, deque
from typing import Dict, List, Optional, AsyncIterator
from datetime import datetime, timedelta

from .config import LLMConfig, ProviderConfig
from .provider import LLMProvider, OpenAIProvider, GeminiProvider, ClaudeProvider
from .request import LLMRequest, LLMResponse, LLMStreamChunk
from ..utils import Logger


class ProviderStats:
    """Statistics for a provider."""
    
    def __init__(self):
        self.requests = 0
        self.successes = 0
        self.failures = 0
        self.total_cost = 0.0
        self.total_latency = 0.0
        self.daily_cost = 0.0
        self.last_reset = datetime.utcnow().date()
        self.rate_limit_remaining = 60
        self.rate_limit_reset = datetime.utcnow()
        self.recent_requests = deque(maxlen=100)  # Last 100 request times
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.requests == 0:
            return 1.0
        return self.successes / self.requests
    
    @property
    def avg_latency(self) -> float:
        """Calculate average latency."""
        if self.successes == 0:
            return 0.0
        return self.total_latency / self.successes
    
    def record_request(self, success: bool, latency: float = 0.0, cost: float = 0.0):
        """Record a request result."""
        now = datetime.utcnow()
        
        # Reset daily cost if new day
        if now.date() > self.last_reset:
            self.daily_cost = 0.0
            self.last_reset = now.date()
        
        self.requests += 1
        self.recent_requests.append(now)
        
        if success:
            self.successes += 1
            self.total_latency += latency
            self.total_cost += cost
            self.daily_cost += cost
        else:
            self.failures += 1
    
    def get_current_rate(self) -> int:
        """Get current request rate per minute."""
        now = datetime.utcnow()
        one_minute_ago = now - timedelta(minutes=1)
        recent = [t for t in self.recent_requests if t > one_minute_ago]
        return len(recent)


class LLMManager:
    """Manager for multiple LLM providers with intelligent routing."""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig.load_from_env()
        self.logger = Logger("LLMManager")
        self.providers: Dict[str, LLMProvider] = {}
        self.stats: Dict[str, ProviderStats] = defaultdict(ProviderStats)
        self.is_initialized = False
        self._lock = asyncio.Lock()
        
        # Provider class mapping
        self.provider_classes = {
            "openai": OpenAIProvider,
            "gemini": GeminiProvider,
            "claude": ClaudeProvider
        }
    
    async def initialize(self) -> bool:
        """Initialize all configured providers."""
        async with self._lock:
            if self.is_initialized:
                return True
            
            self.logger.info("Initializing LLM Manager...")
            
            # Initialize providers
            for name, provider_config in self.config.get_enabled_providers().items():
                if name in self.provider_classes:
                    try:
                        provider_class = self.provider_classes[name]
                        provider = provider_class(provider_config.dict())
                        
                        if await provider.initialize():
                            self.providers[name] = provider
                            self.logger.info(f"Successfully initialized {name} provider")
                        else:
                            self.logger.warning(f"Failed to initialize {name} provider")
                    
                    except Exception as e:
                        self.logger.error(f"Error initializing {name} provider: {str(e)}")
                else:
                    self.logger.warning(f"Unknown provider type: {name}")
            
            if not self.providers:
                self.logger.error("No providers could be initialized")
                return False
            
            self.is_initialized = True
            self.logger.info(f"LLM Manager initialized with {len(self.providers)} providers")
            return True
    
    async def generate(self, request: LLMRequest, preferred_provider: Optional[str] = None) -> LLMResponse:
        """Generate response with automatic provider selection and fallback."""
        if not self.is_initialized:
            if not await self.initialize():
                return LLMResponse(
                    request_id=request.request_id,
                    provider="none",
                    error="No providers available"
                )
        
        # Determine provider order
        providers_to_try = self._get_provider_order(preferred_provider)
        
        last_error = None
        for provider_name in providers_to_try:
            if provider_name not in self.providers:
                continue
            
            provider = self.providers[provider_name]
            provider_config = self.config.providers[provider_name]
            stats = self.stats[provider_name]
            
            # Check rate limits and cost limits
            if not self._can_use_provider(provider_name, stats, provider_config):
                continue
            
            # Try the request
            try:
                start_time = time.time()
                response = await provider.generate(request)
                latency = (time.time() - start_time) * 1000
                
                # Record statistics
                success = response.error is None
                cost = response.usage.estimated_cost if response.usage else 0.0
                stats.record_request(success, latency, cost)
                
                if success:
                    self.logger.debug(f"Request {request.request_id} succeeded with {provider_name}")
                    return response
                else:
                    last_error = response.error
                    self.logger.warning(f"Request {request.request_id} failed with {provider_name}: {response.error}")
                    
            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                stats.record_request(False)
                self.logger.error(f"Exception with {provider_name}: {error_msg}")
        
        # All providers failed
        return LLMResponse(
            request_id=request.request_id,
            provider="failed",
            error=f"All providers failed. Last error: {last_error}"
        )
    
    async def stream_generate(self, request: LLMRequest, preferred_provider: Optional[str] = None) -> AsyncIterator[LLMStreamChunk]:
        """Generate streaming response with provider selection."""
        if not self.is_initialized:
            if not await self.initialize():
                yield LLMStreamChunk(
                    request_id=request.request_id,
                    content="",
                    is_final=True,
                    metadata={"error": "No providers available"}
                )
                return
        
        providers_to_try = self._get_provider_order(preferred_provider)
        
        for provider_name in providers_to_try:
            if provider_name not in self.providers:
                continue
            
            provider = self.providers[provider_name]
            provider_config = self.config.providers[provider_name]
            stats = self.stats[provider_name]
            
            if not self._can_use_provider(provider_name, stats, provider_config):
                continue
            
            try:
                start_time = time.time()
                chunk_count = 0
                
                async for chunk in provider.stream_generate(request):
                    chunk_count += 1
                    yield chunk
                    
                    if chunk.is_final:
                        latency = (time.time() - start_time) * 1000
                        success = chunk.metadata.get("error") is None
                        stats.record_request(success, latency)
                        
                        if success:
                            self.logger.debug(f"Streaming request {request.request_id} succeeded with {provider_name}")
                        return
                        
            except Exception as e:
                stats.record_request(False)
                self.logger.error(f"Streaming exception with {provider_name}: {str(e)}")
        
        # All providers failed
        yield LLMStreamChunk(
            request_id=request.request_id,
            content="",
            is_final=True,
            metadata={"error": "All providers failed for streaming"}
        )
    
    def _get_provider_order(self, preferred_provider: Optional[str] = None) -> List[str]:
        """Get the order of providers to try."""
        available_providers = list(self.providers.keys())
        
        if preferred_provider and preferred_provider in available_providers:
            # Try preferred provider first
            order = [preferred_provider]
            order.extend([p for p in available_providers if p != preferred_provider])
        elif self.config.load_balancing:
            # Use load balancing based on success rate and current load
            order = self._get_load_balanced_order(available_providers)
        else:
            # Use configured fallback order
            order = [p for p in self.config.fallback_order if p in available_providers]
            # Add any providers not in fallback order
            order.extend([p for p in available_providers if p not in order])
        
        return order
    
    def _get_load_balanced_order(self, providers: List[str]) -> List[str]:
        """Get providers ordered by load balancing algorithm."""
        scores = []
        
        for provider_name in providers:
            stats = self.stats[provider_name]
            config = self.config.providers[provider_name]
            
            # Calculate score based on success rate, latency, and current load
            success_rate = stats.success_rate
            avg_latency = stats.avg_latency or 1000  # Default to 1s if no data
            current_rate = stats.get_current_rate()
            rate_limit = config.rate_limit
            
            # Higher success rate = better score
            # Lower latency = better score  
            # Lower current rate = better score
            score = (success_rate * 100) - (avg_latency / 10) - (current_rate / rate_limit * 50)
            
            scores.append((score, provider_name))
        
        # Sort by score (highest first) with some randomization for equal scores
        scores.sort(key=lambda x: (x[0], random.random()), reverse=True)
        return [provider for _, provider in scores]
    
    def _can_use_provider(self, provider_name: str, stats: ProviderStats, config: ProviderConfig) -> bool:
        """Check if a provider can be used based on limits."""
        # Check rate limits
        if stats.get_current_rate() >= config.rate_limit:
            self.logger.debug(f"Rate limit exceeded for {provider_name}")
            return False
        
        # Check daily cost limits
        if config.cost_limit_per_day and stats.daily_cost >= config.cost_limit_per_day:
            self.logger.debug(f"Daily cost limit exceeded for {provider_name}")
            return False
        
        # Check if provider is healthy (basic availability check)
        if stats.requests > 10 and stats.success_rate < 0.1:  # Less than 10% success rate
            self.logger.debug(f"Provider {provider_name} has very low success rate")
            return False
        
        return True
    
    async def estimate_cost(self, request: LLMRequest, provider_name: Optional[str] = None) -> float:
        """Estimate cost for a request."""
        if not self.is_initialized:
            await self.initialize()
        
        if provider_name and provider_name in self.providers:
            return await self.providers[provider_name].estimate_cost(request)
        
        # Get cost from the most likely provider to be used
        providers_to_try = self._get_provider_order(provider_name)
        if providers_to_try and providers_to_try[0] in self.providers:
            return await self.providers[providers_to_try[0]].estimate_cost(request)
        
        return 0.0
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all providers."""
        if not self.is_initialized:
            await self.initialize()
        
        results = {}
        for name, provider in self.providers.items():
            try:
                results[name] = await provider.health_check()
            except Exception as e:
                self.logger.error(f"Health check failed for {name}: {str(e)}")
                results[name] = False
        
        return results
    
    def get_stats(self) -> Dict[str, dict]:
        """Get statistics for all providers."""
        stats_dict = {}
        
        for name, stats in self.stats.items():
            stats_dict[name] = {
                "requests": stats.requests,
                "successes": stats.successes,
                "failures": stats.failures,
                "success_rate": stats.success_rate,
                "avg_latency_ms": stats.avg_latency,
                "total_cost": stats.total_cost,
                "daily_cost": stats.daily_cost,
                "current_rate_per_minute": stats.get_current_rate(),
                "is_available": name in self.providers and self.providers[name].is_available
            }
        
        return stats_dict
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        return list(self.providers.keys())
    
    def get_provider_models(self, provider_name: str) -> List[str]:
        """Get available models for a provider."""
        if provider_name in self.config.providers:
            return self.config.providers[provider_name].models
        return []
    
    async def shutdown(self):
        """Shutdown the manager and clean up resources."""
        self.logger.info("Shutting down LLM Manager...")
        
        # Close provider connections if they have cleanup methods
        for name, provider in self.providers.items():
            if hasattr(provider, 'close'):
                try:
                    await provider.close()
                except Exception as e:
                    self.logger.error(f"Error closing {name} provider: {str(e)}")
        
        self.providers.clear()
        self.is_initialized = False