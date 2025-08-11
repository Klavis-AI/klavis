"""Configuration management for Tavily MCP Server."""
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    """Configuration settings for Tavily MCP Server."""
    
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    MAX_RESULTS_LIMIT = 20
    DEFAULT_MAX_RESULTS = 5
    DEFAULT_SEARCH_DEPTH = "basic"
    DEFAULT_TOPIC = "general"
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.TAVILY_API_KEY:
            logger.error("TAVILY_API_KEY environment variable is required")
            raise ValueError("TAVILY_API_KEY environment variable must be set")
        
        logger.info("Configuration validated successfully")

# Validate configuration on import
Config.validate()