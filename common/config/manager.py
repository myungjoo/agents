#!/usr/bin/env python3
"""
Configuration Manager for AI Agent System
Handles loading, validation, and access to configuration settings
"""

import os
import yaml
import copy
from pathlib import Path
from typing import Any, Dict, Optional, Union
from .validator import ConfigValidator
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Centralized configuration management"""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to configuration file
        """
        self._config: Dict[str, Any] = {}
        self._config_path = config_path
        self._validator = ConfigValidator()
        
        if config_path:
            self.load_config(config_path)
        else:
            self._load_default_config()
    
    def load_config(self, config_path: Union[str, Path]) -> None:
        """
        Load configuration from file
        
        Args:
            config_path: Path to YAML configuration file
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # Validate configuration
            if not self._validator.validate(config_data):
                raise ValueError("Invalid configuration format")
            
            # Merge with environment variables
            self._config = self._merge_env_vars(config_data)
            self._config_path = config_path
            
            logger.info(f"Configuration loaded from {config_path}")
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {e}")
    
    def _load_default_config(self) -> None:
        """Load default configuration"""
        default_config = {
            "system": {
                "name": "AI Code Audit System",
                "version": "1.0.0",
                "environment": "development",
                "log_level": "INFO",
                "data_dir": "data",
                "temp_dir": "/tmp/ai-audit",
                "max_workers": 2
            },
            "database": {
                "type": "sqlite",
                "sqlite": {"path": "data/audit.db"}
            },
            "llm": {
                "default_provider": "openai",
                "openai": {
                    "model": "gpt-4-turbo-preview",
                    "max_tokens": 4000,
                    "temperature": 0.1
                }
            },
            "web": {
                "host": "127.0.0.1",
                "port": 8080,
                "auth_required": False
            },
            "agents": {
                "default_timeout": 3600,
                "max_concurrent": 2
            }
        }
        
        self._config = self._merge_env_vars(default_config)
        logger.info("Loaded default configuration")
    
    def _merge_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge environment variables into configuration
        
        Args:
            config: Base configuration dictionary
            
        Returns:
            Configuration with environment variables merged
        """
        env_config = copy.deepcopy(config)
        
        # Map environment variables to config paths
        env_mappings = {
            "AI_AUDIT_LOG_LEVEL": ["system", "log_level"],
            "AI_AUDIT_WEB_PORT": ["web", "port"],
            "AI_AUDIT_DB_PATH": ["database", "sqlite", "path"],
            "OPENAI_API_KEY": ["llm", "openai", "api_key"],
            "GEMINI_API_KEY": ["llm", "gemini", "api_key"],
            "ANTHROPIC_API_KEY": ["llm", "anthropic", "api_key"],
            "AI_AUDIT_SECRET_KEY": ["web", "secret_key"],
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                self._set_nested_value(env_config, config_path, self._convert_type(value))
        
        return env_config
    
    def _set_nested_value(self, config: Dict[str, Any], path: list, value: Any) -> None:
        """Set value in nested dictionary"""
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def _convert_type(self, value: str) -> Any:
        """Convert string value to appropriate type"""
        # Try boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Try integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated path
        
        Args:
            key_path: Dot-separated path (e.g., "system.log_level")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        current = self._config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value by dot-separated path
        
        Args:
            key_path: Dot-separated path
            value: Value to set
        """
        keys = key_path.split('.')
        self._set_nested_value(self._config, keys, value)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section
        
        Args:
            section: Section name
            
        Returns:
            Section configuration dictionary
        """
        return self._config.get(section, {})
    
    def validate(self) -> bool:
        """
        Validate current configuration
        
        Returns:
            True if configuration is valid
        """
        return self._validator.validate(self._config)
    
    def save(self, config_path: Optional[Union[str, Path]] = None) -> None:
        """
        Save configuration to file
        
        Args:
            config_path: Path to save configuration (defaults to current config path)
        """
        if config_path:
            save_path = Path(config_path)
        elif self._config_path:
            save_path = Path(self._config_path)
        else:
            raise ValueError("No configuration path specified")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, default_flow_style=False, indent=2)
        
        logger.info(f"Configuration saved to {save_path}")
    
    def reload(self) -> None:
        """Reload configuration from file"""
        if self._config_path:
            self.load_config(self._config_path)
        else:
            self._load_default_config()
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get read-only copy of configuration"""
        return copy.deepcopy(self._config)
    
    def __getitem__(self, key: str) -> Any:
        """Get configuration value by key"""
        return self.get(key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set configuration value by key"""
        self.set(key, value)