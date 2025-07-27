"""
Configuration for Zapier MCP Server.

This module contains the configuration management using Pydantic settings
for environment-based configuration.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ZapierConfig(BaseSettings):
    """
    Configuration for Zapier MCP Server.
    
    This class manages all configuration settings using Pydantic settings
    with environment variable support.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # API Configuration
    api_key: str = Field(..., description="Zapier API key")
    api_base_url: str = Field(
        default="https://api.zapier.com/v1",
        description="Zapier API base URL"
    )
    api_timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="API request timeout in seconds"
    )
    
    # Server Configuration
    server_host: str = Field(
        default="localhost",
        description="Server host"
    )
    server_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port"
    )
    server_debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        description="Logging level"
    )
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Logging format"
    )
    log_file: Optional[str] = Field(
        default=None,
        description="Log file path (optional)"
    )
    
    # Caching Configuration
    cache_max_size: int = Field(
        default=1000,
        ge=1,
        le=10000,
        description="Maximum cache size"
    )
    cache_ttl: int = Field(
        default=300,
        ge=1,
        le=3600,
        description="Cache TTL in seconds"
    )
    cache_enabled: bool = Field(
        default=True,
        description="Enable caching"
    )
    
    # Rate Limiting Configuration
    rate_limit_max_calls: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum API calls per time window"
    )
    rate_limit_window: int = Field(
        default=60,
        ge=1,
        le=3600,
        description="Rate limit time window in seconds"
    )
    
    # Retry Configuration
    retry_max_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum retry attempts"
    )
    retry_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=60.0,
        description="Retry delay in seconds"
    )
    retry_backoff: float = Field(
        default=2.0,
        ge=1.0,
        le=10.0,
        description="Retry backoff multiplier"
    )
    
    # Circuit Breaker Configuration
    circuit_breaker_failure_threshold: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Circuit breaker failure threshold"
    )
    circuit_breaker_recovery_timeout: int = Field(
        default=60,
        ge=1,
        le=3600,
        description="Circuit breaker recovery timeout in seconds"
    )
    
    # Security Configuration
    enable_ssl: bool = Field(
        default=True,
        description="Enable SSL/TLS"
    )
    ssl_cert_file: Optional[str] = Field(
        default=None,
        description="SSL certificate file path"
    )
    ssl_key_file: Optional[str] = Field(
        default=None,
        description="SSL private key file path"
    )
    
    # Monitoring Configuration
    enable_metrics: bool = Field(
        default=True,
        description="Enable metrics collection"
    )
    metrics_port: int = Field(
        default=9090,
        ge=1,
        le=65535,
        description="Metrics server port"
    )
    
    # Health Check Configuration
    health_check_enabled: bool = Field(
        default=True,
        description="Enable health checks"
    )
    health_check_interval: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Health check interval in seconds"
    )
    
    def validate_config(self) -> bool:
        """
        Validate the configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Validate API key
            if not self.api_key or len(self.api_key) < 10:
                raise ValueError("API key must be at least 10 characters long")
            
            # Validate SSL configuration
            if self.enable_ssl:
                if not self.ssl_cert_file or not self.ssl_key_file:
                    raise ValueError("SSL certificate and key files are required when SSL is enabled")
                
                if not os.path.exists(self.ssl_cert_file):
                    raise ValueError(f"SSL certificate file not found: {self.ssl_cert_file}")
                
                if not os.path.exists(self.ssl_key_file):
                    raise ValueError(f"SSL private key file not found: {self.ssl_key_file}")
            
            # Validate log file
            if self.log_file and not os.path.exists(os.path.dirname(self.log_file)):
                raise ValueError(f"Log file directory does not exist: {os.path.dirname(self.log_file)}")
            
            return True
            
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            return False
    
    def get_api_headers(self) -> dict:
        """Get API headers for requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Zapier-MCP-Server/1.0.0"
        }
    
    def get_cache_config(self) -> dict:
        """Get cache configuration."""
        return {
            "max_size": self.cache_max_size,
            "ttl": self.cache_ttl,
            "enabled": self.cache_enabled
        }
    
    def get_retry_config(self) -> dict:
        """Get retry configuration."""
        return {
            "max_attempts": self.retry_max_attempts,
            "delay": self.retry_delay,
            "backoff": self.retry_backoff
        }
    
    def get_rate_limit_config(self) -> dict:
        """Get rate limiting configuration."""
        return {
            "max_calls": self.rate_limit_max_calls,
            "window": self.rate_limit_window
        }
    
    def get_circuit_breaker_config(self) -> dict:
        """Get circuit breaker configuration."""
        return {
            "failure_threshold": self.circuit_breaker_failure_threshold,
            "recovery_timeout": self.circuit_breaker_recovery_timeout
        }
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "api": {
                "base_url": self.api_base_url,
                "timeout": self.api_timeout
            },
            "server": {
                "host": self.server_host,
                "port": self.server_port,
                "debug": self.server_debug
            },
            "logging": {
                "level": self.log_level,
                "format": self.log_format,
                "file": self.log_file
            },
            "caching": self.get_cache_config(),
            "rate_limiting": self.get_rate_limit_config(),
            "retry": self.get_retry_config(),
            "circuit_breaker": self.get_circuit_breaker_config(),
            "security": {
                "enable_ssl": self.enable_ssl,
                "ssl_cert_file": self.ssl_cert_file,
                "ssl_key_file": self.ssl_key_file
            },
            "monitoring": {
                "enable_metrics": self.enable_metrics,
                "metrics_port": self.metrics_port
            },
            "health_check": {
                "enabled": self.health_check_enabled,
                "interval": self.health_check_interval
            }
        } 