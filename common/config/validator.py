#!/usr/bin/env python3
"""
Configuration Validator for AI Agent System
Validates configuration structure and required fields
"""

from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validates configuration structure and values"""
    
    def __init__(self):
        """Initialize validator with schema definitions"""
        self._schema = self._build_schema()
    
    def _build_schema(self) -> Dict[str, Any]:
        """Build configuration schema for validation"""
        return {
            "system": {
                "required": ["name", "version", "environment"],
                "optional": ["log_level", "data_dir", "temp_dir", "max_workers"],
                "types": {
                    "name": str,
                    "version": str,
                    "environment": str,
                    "log_level": str,
                    "data_dir": str,
                    "temp_dir": str,
                    "max_workers": int
                },
                "values": {
                    "environment": ["development", "staging", "production"],
                    "log_level": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                }
            },
            "database": {
                "required": ["type"],
                "optional": ["sqlite", "postgresql"],
                "types": {
                    "type": str
                },
                "values": {
                    "type": ["sqlite", "postgresql"]
                }
            },
            "llm": {
                "required": ["default_provider"],
                "optional": ["openai", "gemini", "anthropic", "custom"],
                "types": {
                    "default_provider": str
                },
                "values": {
                    "default_provider": ["openai", "gemini", "anthropic", "custom"]
                }
            },
            "web": {
                "required": ["host", "port"],
                "optional": ["secret_key", "cors_origins", "auth_required", "session_timeout"],
                "types": {
                    "host": str,
                    "port": int,
                    "secret_key": str,
                    "cors_origins": list,
                    "auth_required": bool,
                    "session_timeout": int
                }
            },
            "agents": {
                "required": ["default_timeout"],
                "optional": ["max_concurrent", "restart_on_failure", "repo_analyzer", "issue_finder", "code_tester", "report_generator"],
                "types": {
                    "default_timeout": int,
                    "max_concurrent": int,
                    "restart_on_failure": bool
                }
            }
        }
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration against schema
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if configuration is valid
        """
        try:
            errors = []
            
            # Check top-level sections
            for section_name, section_schema in self._schema.items():
                if section_name not in config:
                    # Check if section has required fields
                    if section_schema.get("required"):
                        errors.append(f"Missing required section: {section_name}")
                    continue
                
                section_config = config[section_name]
                section_errors = self._validate_section(section_name, section_config, section_schema)
                errors.extend(section_errors)
            
            # Validate specific LLM provider configurations
            if "llm" in config:
                llm_errors = self._validate_llm_providers(config["llm"])
                errors.extend(llm_errors)
            
            # Validate database configurations
            if "database" in config:
                db_errors = self._validate_database_config(config["database"])
                errors.extend(db_errors)
            
            if errors:
                for error in errors:
                    logger.error(f"Configuration validation error: {error}")
                return False
            
            logger.info("Configuration validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    def _validate_section(self, section_name: str, section_config: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """Validate a configuration section"""
        errors = []
        
        # Check required fields
        for field in schema.get("required", []):
            if field not in section_config:
                errors.append(f"Missing required field in {section_name}: {field}")
        
        # Check field types and values
        types = schema.get("types", {})
        values = schema.get("values", {})
        
        for field, value in section_config.items():
            # Type checking
            if field in types:
                expected_type = types[field]
                if not isinstance(value, expected_type):
                    errors.append(f"Invalid type for {section_name}.{field}: expected {expected_type.__name__}, got {type(value).__name__}")
            
            # Value validation
            if field in values:
                allowed_values = values[field]
                if value not in allowed_values:
                    errors.append(f"Invalid value for {section_name}.{field}: {value} not in {allowed_values}")
        
        return errors
    
    def _validate_llm_providers(self, llm_config: Dict[str, Any]) -> List[str]:
        """Validate LLM provider configurations"""
        errors = []
        
        default_provider = llm_config.get("default_provider")
        if not default_provider:
            return errors
        
        # Check if default provider configuration exists
        if default_provider not in llm_config:
            errors.append(f"Configuration for default LLM provider '{default_provider}' not found")
            return errors
        
        provider_config = llm_config[default_provider]
        
        # Validate provider-specific required fields
        required_fields = {
            "openai": ["api_key", "model"],
            "gemini": ["api_key", "model"],
            "anthropic": ["api_key", "model"],
            "custom": ["api_key", "base_url", "model"]
        }
        
        if default_provider in required_fields:
            for field in required_fields[default_provider]:
                if field not in provider_config:
                    errors.append(f"Missing required field in llm.{default_provider}: {field}")
        
        return errors
    
    def _validate_database_config(self, db_config: Dict[str, Any]) -> List[str]:
        """Validate database configuration"""
        errors = []
        
        db_type = db_config.get("type")
        if not db_type:
            return errors
        
        # Check type-specific configuration
        if db_type == "sqlite":
            if "sqlite" not in db_config:
                errors.append("Missing sqlite configuration for database type 'sqlite'")
            elif "path" not in db_config["sqlite"]:
                errors.append("Missing required field in database.sqlite: path")
        
        elif db_type == "postgresql":
            if "postgresql" not in db_config:
                errors.append("Missing postgresql configuration for database type 'postgresql'")
            else:
                required_pg_fields = ["host", "port", "database", "username", "password"]
                pg_config = db_config["postgresql"]
                for field in required_pg_fields:
                    if field not in pg_config:
                        errors.append(f"Missing required field in database.postgresql: {field}")
        
        return errors
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the validation schema"""
        return self._schema.copy()
    
    def validate_field(self, section: str, field: str, value: Any) -> bool:
        """
        Validate a single field value
        
        Args:
            section: Configuration section name
            field: Field name
            value: Field value
            
        Returns:
            True if field is valid
        """
        if section not in self._schema:
            return True  # Unknown sections are allowed
        
        section_schema = self._schema[section]
        
        # Check type
        types = section_schema.get("types", {})
        if field in types:
            expected_type = types[field]
            if not isinstance(value, expected_type):
                return False
        
        # Check allowed values
        values = section_schema.get("values", {})
        if field in values:
            allowed_values = values[field]
            if value not in allowed_values:
                return False
        
        return True