"""
Logging configuration for Exa MCP Server
"""

import logging
import sys
from typing import Optional
from .config import get_config


def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """
    Set up logging for the Exa MCP Server
    
    Args:
        log_level: Override the default log level
        
    Returns:
        Configured logger instance
    """
    config = get_config()
    level = log_level or config.log_level
    
    # Configure logging format
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Configure handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    # Configure logger
    logger = logging.getLogger("exa-mcp-server")
    logger.setLevel(getattr(logging, level.upper()))
    logger.addHandler(handler)
    
    # Prevent duplicate logs
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module
    
    Args:
        name: Name of the module/component
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"exa-mcp-server.{name}")


# Initialize default logger
logger = setup_logging()