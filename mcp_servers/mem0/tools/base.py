import logging
import os
from mem0 import MemoryClient
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Default configuration
DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID", "mem0_mcp")
CUSTOM_INSTRUCTIONS = """
Extract the Following Information:  

- Code Snippets: Save the actual code for future reference and analysis.  
- Explanation: Document a clear description of what the code does, its purpose, and implementation details.
- Technical Context: Include information about programming languages, frameworks, libraries, dependencies, and system requirements.  
- Key Features: Highlight main functionalities, important methods, design patterns, and notable implementation aspects.
- Usage Context: Document how and when the code should be used, including any prerequisites or constraints.
"""

def get_user_id() -> str:
    """Get the current user identifier for memory operations."""
    logger.debug(f"DEFAULT_USER_ID: {DEFAULT_USER_ID}")
    return DEFAULT_USER_ID

def initialize_mem0_client() -> MemoryClient:
    """Initialize and configure the mem0 client with custom instructions for AI-assisted development."""
    try:
        client = MemoryClient()
        client.update_project(custom_instructions=CUSTOM_INSTRUCTIONS)
        logger.info("mem0 client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize mem0 client: {e}")
        raise

# Global client instance for memory operations
mem0_client = initialize_mem0_client()
