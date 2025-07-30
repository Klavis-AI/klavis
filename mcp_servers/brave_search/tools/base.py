import logging
import os
from contextvars import ContextVar
from typing import Optional
from dotenv import load_dotenv

# Load env vars from .env
load_dotenv()

logger = logging.getLogger(__name__)

# Context variable to store the auth token per request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

def get_auth_token() -> str:
    """
    Get the Brave API token from context or fallback to env.
    """
    try:
        token = auth_token_context.get()
        if not token:
            # Fallback to environment variable
            token = os.getenv("BRAVE_SEARCH_API_KEY")
            logger.debug(f"Using token from environment: {token}")
            if not token:
                raise RuntimeError("No Brave auth token found in context or environment")
        return token
    except LookupError:
        # Context variable not set at all
        token = os.getenv("BRAVE_SEARCH_API_KEY")
        if not token:
            raise RuntimeError("No Brave auth token found in context or environment")
        return token

def get_brave_client() -> Optional[dict]:
    """
    Return a Brave client config (e.g., base_url and headers) ready to use.
    """
    try:
        auth_token = get_auth_token()
        client = auth_token
        return client
    except RuntimeError as e:
        logger.warning(f"Failed to get Brave auth token: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Brave client: {e}")
        return None
