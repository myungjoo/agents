"""
Configuration utility for the AI Agent System.
"""

import os
import yaml
import json
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Configuration manager for the AI Agent System."""
    
    _instance: Optional['Config'] = None
    _config: Dict[str, Any] = {}
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._load_config()
            Config._initialized = True
    
    def _load_config(self):
        """Load configuration from environment and config files."""
        # Load environment variables
        load_dotenv('config/.env')
        
        # Load from environment variables
        self._config.update({
            'system': {
                'name': os.getenv('SYSTEM_NAME', 'AI_Agent_System'),
                'log_level': os.getenv('LOG_LEVEL', 'INFO'),
                'data_dir': os.getenv('DATA_DIR', '/var/lib/ai_agents'),
                'temp_dir': os.getenv('TEMP_DIR', '/tmp/ai_agents')
            },
            'web': {
                'host': os.getenv('WEB_HOST', '0.0.0.0'),
                'port': int(os.getenv('WEB_PORT', '8080')),
                'secret_key': os.getenv('WEB_SECRET_KEY', 'your-secret-key-here')
            },
            'database': {
                'url': os.getenv('DATABASE_URL', 'sqlite:///data/agents.db')
            },
            'llm': {
                'primary_provider': os.getenv('PRIMARY_LLM_PROVIDER', 'openai'),
                'providers': {
                    'openai': {
                        'api_key': os.getenv('OPENAI_API_KEY'),
                        'model': os.getenv('OPENAI_MODEL', 'gpt-4'),
                        'max_tokens': int(os.getenv('OPENAI_MAX_TOKENS', '4000')),
                        'temperature': float(os.getenv('OPENAI_TEMPERATURE', '0.1'))
                    },
                    'gemini': {
                        'api_key': os.getenv('GEMINI_API_KEY'),
                        'model': os.getenv('GEMINI_MODEL', 'gemini-pro'),
                        'max_tokens': int(os.getenv('GEMINI_MAX_TOKENS', '4000')),
                        'temperature': float(os.getenv('GEMINI_TEMPERATURE', '0.1'))
                    },
                    'claude': {
                        'api_key': os.getenv('CLAUDE_API_KEY'),
                        'model': os.getenv('CLAUDE_MODEL', 'claude-3-sonnet-20240229'),
                        'max_tokens': int(os.getenv('CLAUDE_MAX_TOKENS', '4000')),
                        'temperature': float(os.getenv('CLAUDE_TEMPERATURE', '0.1'))
                    },
                    'custom': {
                        'endpoint': os.getenv('CUSTOM_LLM_ENDPOINT'),
                        'api_key': os.getenv('CUSTOM_LLM_API_KEY'),
                        'model': os.getenv('CUSTOM_LLM_MODEL', 'custom-model'),
                        'request_format': os.getenv('CUSTOM_LLM_FORMAT', 'openai')
                    }
                }
            },
            'github': {
                'token': os.getenv('GITHUB_TOKEN'),
                'username': os.getenv('GITHUB_USERNAME')
            },
            'agents': {
                'max_concurrent': int(os.getenv('MAX_CONCURRENT_AGENTS', '5')),
                'timeout': int(os.getenv('AGENT_TIMEOUT', '3600')),
                'memory_limit': os.getenv('AGENT_MEMORY_LIMIT', '2GB')
            },
            'analysis': {
                'timeout': int(os.getenv('ANALYSIS_TIMEOUT', '1800')),
                'max_repo_size_mb': int(os.getenv('MAX_REPO_SIZE_MB', '1000')),
                'supported_languages': os.getenv('SUPPORTED_LANGUAGES', 'c,cpp,python,java,javascript,typescript,go,rust').split(',')
            },
            'testing': {
                'timeout': int(os.getenv('TEST_TIMEOUT', '300')),
                'memory_limit': os.getenv('TEST_MEMORY_LIMIT', '1GB'),
                'cpu_limit': int(os.getenv('TEST_CPU_LIMIT', '2'))
            },
            'mcp': {
                'enabled': os.getenv('MCP_ENABLED', 'true').lower() == 'true',
                'server_url': os.getenv('MCP_SERVER_URL', 'http://localhost:3000')
            },
            'a2a': {
                'enabled': os.getenv('A2A_ENABLED', 'true').lower() == 'true',
                'server_url': os.getenv('A2A_SERVER_URL', 'http://localhost:4000')
            },
            'logging': {
                'log_file': os.getenv('LOG_FILE', '/var/log/ai_agents/system.log'),
                'max_size': os.getenv('LOG_MAX_SIZE', '100MB'),
                'backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5'))
            },
            'security': {
                'enable_ssl': os.getenv('ENABLE_SSL', 'false').lower() == 'true',
                'ssl_cert_file': os.getenv('SSL_CERT_FILE', ''),
                'ssl_key_file': os.getenv('SSL_KEY_FILE', ''),
                'allowed_hosts': os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
            },
            'performance': {
                'worker_processes': int(os.getenv('WORKER_PROCESSES', '4')),
                'worker_threads': int(os.getenv('WORKER_THREADS', '2')),
                'cache_ttl': int(os.getenv('CACHE_TTL', '3600'))
            }
        })
        
        # Load additional config files if they exist
        self._load_config_files()
    
    def _load_config_files(self):
        """Load configuration from YAML and JSON files."""
        config_files = [
            'config/config.yaml',
            'config/config.yml',
            'config/config.json'
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        if config_file.endswith(('.yaml', '.yml')):
                            file_config = yaml.safe_load(f)
                        else:
                            file_config = json.load(f)
                    
                    # Merge with existing config
                    self._merge_config(self._config, file_config)
                except Exception as e:
                    print(f"Warning: Could not load config file {config_file}: {e}")
    
    def _merge_config(self, base: Dict[str, Any], update: Dict[str, Any]):
        """Recursively merge configuration dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set a configuration value using dot notation."""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_llm_config(self, provider: str) -> Dict[str, Any]:
        """Get LLM provider configuration."""
        return self._config['llm']['providers'].get(provider, {})
    
    def get_system_config(self) -> Dict[str, Any]:
        """Get system configuration."""
        return self._config['system']
    
    def get_web_config(self) -> Dict[str, Any]:
        """Get web interface configuration."""
        return self._config['web']
    
    def get_agent_config(self) -> Dict[str, Any]:
        """Get agent configuration."""
        return self._config['agents']
    
    def is_provider_configured(self, provider: str) -> bool:
        """Check if a provider is properly configured."""
        provider_config = self.get_llm_config(provider)
        
        if provider == 'custom':
            return bool(provider_config.get('endpoint') and provider_config.get('api_key'))
        else:
            return bool(provider_config.get('api_key'))
    
    def save_config(self, filepath: str = None):
        """Save current configuration to file."""
        if filepath is None:
            filepath = 'config/config.yaml'
        
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"Error saving config to {filepath}: {e}")
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return validation results."""
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required configurations
        if not self.get('llm.primary_provider'):
            validation['errors'].append("Primary LLM provider not configured")
            validation['valid'] = False
        
        # Check if primary provider is configured
        primary_provider = self.get('llm.primary_provider')
        if not self.is_provider_configured(primary_provider):
            validation['errors'].append(f"Primary provider '{primary_provider}' not properly configured")
            validation['valid'] = False
        
        # Check web configuration
        if not self.get('web.secret_key') or self.get('web.secret_key') == 'your-secret-key-here':
            validation['warnings'].append("Web secret key not set - using default")
        
        # Check GitHub configuration for PR creation
        if not self.get('github.token'):
            validation['warnings'].append("GitHub token not configured - PR creation will not work")
        
        return validation