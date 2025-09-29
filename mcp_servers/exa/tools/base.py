import logging
import os
from contextvars import ContextVar
from typing import Optional
from dotenv import load_dotenv
from exa_py import Exa

# Load env vars from .env
load_dotenv()

logger = logging.getLogger(__name__)

# Context variable to store the auth token per request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

def get_auth_token() -> str:
    """
    Get the Exa API token from context or fallback to env.
    """
    try:
        token = auth_token_context.get()
        if not token:
            # Fallback to environment variable
            token = os.getenv("EXA_API_KEY")
            logger.debug(f"Using token from environment: {'***' if token else 'None'}")
            if not token:
                raise RuntimeError("No Exa auth token found in context or environment")
        return token
    except LookupError:
        # Context variable not set at all
        token = os.getenv("EXA_API_KEY")
        if not token:
            raise RuntimeError("No Exa auth token found in context or environment")
        return token

def get_exa_client() -> Optional[Exa]:
    """
    Return an Exa client instance ready to use.
    """
    try:
        auth_token = get_auth_token()
        client = Exa(api_key=auth_token)
        return client
    except RuntimeError as e:
        logger.warning(f"Failed to get Exa auth token: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Exa client: {e}")
        return None
