"""
Configuration management for Exa MCP Server
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class ExaConfig(BaseSettings):
    """Configuration settings for Exa MCP Server"""
    
    # API Configuration
    exa_api_key: str = Field(..., env="EXA_API_KEY")
    exa_base_url: str = Field("https://api.exa.ai", env="EXA_BASE_URL")
    
    # Server Configuration
    server_name: str = Field("exa-mcp-server", env="SERVER_NAME")
    server_version: str = Field("1.0.0", env="SERVER_VERSION")
    
    # Request Configuration
    default_timeout: int = Field(30, env="DEFAULT_TIMEOUT")
    max_retries: int = Field(3, env="MAX_RETRIES")
    
    # Logging Configuration
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }


# Global configuration instance
config = ExaConfig()


def get_config() -> ExaConfig:
    """Get the current configuration instance"""
    return config


def validate_config() -> bool:
    """Validate that all required configuration is present"""
    try:
        config = get_config()
        if not config.exa_api_key:
            raise ValueError("EXA_API_KEY is required")
        if len(config.exa_api_key) < 10:
            raise ValueError("EXA_API_KEY appears to be too short")
        return True
    except Exception as e:
        print(f"Configuration validation failed: {e}")
        return False