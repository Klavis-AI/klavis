import logging
import os
from contextvars import ContextVar
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

auth_token_context: ContextVar[str] = ContextVar('auth_token')

def get_auth_token() -> str:
    try:
        token = auth_token_context.get()
        if not token:
            token = os.getenv("APOLLO_API_KEY")
            if not token:
                raise RuntimeError("No authentication token available")
        return token
    except LookupError:
        token = os.getenv("APOLLO_API_KEY")
        if not token:
            raise RuntimeError("Authentication token not found in context or environment")
        return token

def get_apollo_client() -> Optional[dict]:
    """
    Return a simple client dict with base_url and headers.
    """
    try:
        auth_token = get_auth_token()
        client = {
            "accept": "application/json",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "x-api-key": auth_token
        }
        return client
    except RuntimeError as e:
        logger.warning(f"Failed to get auth token: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Apollo client: {e}")
        return None