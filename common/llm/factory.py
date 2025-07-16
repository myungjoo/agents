"""
LLM Provider Factory

Factory class for creating and managing different LLM providers.
"""

from typing import Dict, Any, Optional
import os
from .base import LLMProvider, LLMProviderType
from .providers import OpenAIProvider, GeminiProvider, ClaudeProvider, CustomProvider


class LLMFactory:
    """Factory for creating LLM providers."""
    
    _providers: Dict[str, LLMProvider] = {}
    _primary_provider: Optional[LLMProvider] = None
    
    @classmethod
    def create_provider(cls, provider_type: str, config: Dict[str, Any]) -> LLMProvider:
        """Create a new LLM provider instance."""
        provider_type_enum = LLMProviderType(provider_type.lower())
        
        if provider_type_enum == LLMProviderType.OPENAI:
            return OpenAIProvider(config)
        elif provider_type_enum == LLMProviderType.GEMINI:
            return GeminiProvider(config)
        elif provider_type_enum == LLMProviderType.CLAUDE:
            return ClaudeProvider(config)
        elif provider_type_enum == LLMProviderType.CUSTOM:
            return CustomProvider(config)
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
    
    @classmethod
    def get_provider(cls, provider_type: str) -> Optional[LLMProvider]:
        """Get a cached provider instance."""
        return cls._providers.get(provider_type)
    
    @classmethod
    def get_primary_provider(cls) -> Optional[LLMProvider]:
        """Get the primary LLM provider."""
        return cls._primary_provider
    
    @classmethod
    def set_primary_provider(cls, provider: LLMProvider):
        """Set the primary LLM provider."""
        cls._primary_provider = provider
    
    @classmethod
    def register_provider(cls, provider_type: str, provider: LLMProvider):
        """Register a provider instance."""
        cls._providers[provider_type] = provider
    
    @classmethod
    def initialize_from_env(cls) -> Dict[str, LLMProvider]:
        """Initialize providers from environment variables."""
        providers = {}
        
        # Get primary provider type
        primary_type = os.getenv('PRIMARY_LLM_PROVIDER', 'openai').lower()
        
        # Initialize OpenAI provider
        if os.getenv('OPENAI_API_KEY'):
            openai_config = {
                'api_key': os.getenv('OPENAI_API_KEY'),
                'model': os.getenv('OPENAI_MODEL', 'gpt-4'),
                'max_tokens': int(os.getenv('OPENAI_MAX_TOKENS', '4000')),
                'temperature': float(os.getenv('OPENAI_TEMPERATURE', '0.1'))
            }
            openai_provider = OpenAIProvider(openai_config)
            providers['openai'] = openai_provider
            cls.register_provider('openai', openai_provider)
            
            if primary_type == 'openai':
                cls.set_primary_provider(openai_provider)
        
        # Initialize Gemini provider
        if os.getenv('GEMINI_API_KEY'):
            gemini_config = {
                'api_key': os.getenv('GEMINI_API_KEY'),
                'model': os.getenv('GEMINI_MODEL', 'gemini-pro'),
                'max_tokens': int(os.getenv('GEMINI_MAX_TOKENS', '4000')),
                'temperature': float(os.getenv('GEMINI_TEMPERATURE', '0.1'))
            }
            gemini_provider = GeminiProvider(gemini_config)
            providers['gemini'] = gemini_provider
            cls.register_provider('gemini', gemini_provider)
            
            if primary_type == 'gemini':
                cls.set_primary_provider(gemini_provider)
        
        # Initialize Claude provider
        if os.getenv('CLAUDE_API_KEY'):
            claude_config = {
                'api_key': os.getenv('CLAUDE_API_KEY'),
                'model': os.getenv('CLAUDE_MODEL', 'claude-3-sonnet-20240229'),
                'max_tokens': int(os.getenv('CLAUDE_MAX_TOKENS', '4000')),
                'temperature': float(os.getenv('CLAUDE_TEMPERATURE', '0.1'))
            }
            claude_provider = ClaudeProvider(claude_config)
            providers['claude'] = claude_provider
            cls.register_provider('claude', claude_provider)
            
            if primary_type == 'claude':
                cls.set_primary_provider(claude_provider)
        
        # Initialize Custom provider
        if os.getenv('CUSTOM_LLM_ENDPOINT') and os.getenv('CUSTOM_LLM_API_KEY'):
            custom_config = {
                'endpoint': os.getenv('CUSTOM_LLM_ENDPOINT'),
                'api_key': os.getenv('CUSTOM_LLM_API_KEY'),
                'model': os.getenv('CUSTOM_LLM_MODEL', 'custom-model'),
                'request_format': os.getenv('CUSTOM_LLM_FORMAT', 'openai')
            }
            custom_provider = CustomProvider(custom_config)
            providers['custom'] = custom_provider
            cls.register_provider('custom', custom_provider)
            
            if primary_type == 'custom':
                cls.set_primary_provider(custom_provider)
        
        # If no primary provider was set, use the first available one
        if cls._primary_provider is None and providers:
            first_provider = list(providers.values())[0]
            cls.set_primary_provider(first_provider)
        
        return providers
    
    @classmethod
    def get_available_providers(cls) -> Dict[str, Dict[str, Any]]:
        """Get information about all available providers."""
        info = {}
        
        for provider_type, provider in cls._providers.items():
            info[provider_type] = {
                'available': provider.is_available(),
                'usage_info': provider.get_usage_info(),
                'is_primary': provider == cls._primary_provider
            }
        
        return info
    
    @classmethod
    def switch_primary_provider(cls, provider_type: str) -> bool:
        """Switch the primary provider."""
        provider = cls._providers.get(provider_type)
        if provider and provider.is_available():
            cls.set_primary_provider(provider)
            return True
        return False
    
    @classmethod
    def test_provider(cls, provider_type: str) -> Dict[str, Any]:
        """Test a provider with a simple prompt."""
        provider = cls._providers.get(provider_type)
        if not provider:
            return {'error': f'Provider {provider_type} not found'}
        
        if not provider.is_available():
            return {'error': f'Provider {provider_type} is not available'}
        
        try:
            import asyncio
            from .base import LLMRequest
            
            # Create a simple test request
            request = LLMRequest(
                prompt="Hello, this is a test message. Please respond with 'Test successful'.",
                system_message="You are a helpful assistant. Keep responses brief and to the point."
            )
            
            # Run the test
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(provider.call(request))
            loop.close()
            
            return {
                'success': True,
                'response': response.content,
                'response_time': response.response_time,
                'model': response.model,
                'usage': response.usage
            }
            
        except Exception as e:
            return {'error': str(e)}