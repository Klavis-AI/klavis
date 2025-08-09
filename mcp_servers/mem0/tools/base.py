import logging
import os
from contextvars import ContextVar
from mem0 import MemoryClient
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID", "mem0_mcp")
CUSTOM_INSTRUCTIONS = """
Extract the Following Information:  

- Code Snippets: Save the actual code for future reference and analysis.  
- Explanation: Document a clear description of what the code does, its purpose, and implementation details.
- Technical Context: Include information about programming languages, frameworks, libraries, dependencies, and system requirements.  
- Key Features: Highlight main functionalities, important methods, design patterns, and notable implementation aspects.
- Usage Context: Document how and when the code should be used, including any prerequisites or constraints.
"""

mem0_api_key_context: ContextVar[str] = ContextVar('mem0_api_key')

def get_mem0_api_key() -> str:
    """Get the mem0 API key from context or environment."""
    try:
        return mem0_api_key_context.get()
    except LookupError:
        api_key = os.getenv("MEM0_API_KEY")
        if not api_key:
            raise RuntimeError("mem0 API key not found in request context or environment")
        return api_key

def get_user_id() -> str:
    """Get the current user identifier for memory operations."""
    logger.debug(f"DEFAULT_USER_ID: {DEFAULT_USER_ID}")
    return DEFAULT_USER_ID

def get_mem0_client() -> MemoryClient:
    """Get a configured mem0 client with current API key from context."""
    try:
        api_key = get_mem0_api_key()
        client = MemoryClient(api_key=api_key)
        client.update_project(custom_instructions=CUSTOM_INSTRUCTIONS)
        logger.debug("mem0 client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize mem0 client: {e}")
        raise
