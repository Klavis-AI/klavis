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
            # Fallback to environment variable if no token in context
            token = os.getenv("CAL_COM_API_KEY")
            if not token:
                raise RuntimeError("No authentication token available")
        return token
    except LookupError:
        token = os.getenv("CAL_COM_API_KEY")
        if not token:
            raise RuntimeError("Authentication token not found in context or environment")
        return token

def get_calcom_client() -> Optional[dict]:
    """
    Return a simple client dict with base_url and headers.
    """
    try:
        auth_token = get_auth_token()
        client = auth_token
        return client
    except RuntimeError as e:
        logger.warning(f"Failed to get auth token: {e}")
        return None