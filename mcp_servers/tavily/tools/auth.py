import os
import logging
from contextvars import ContextVar

from dotenv import load_dotenv
from tavily import TavilyClient

logger = logging.getLogger(__name__)

# Load environment variables from .env if present
load_dotenv()

tavily_api_key_context: ContextVar[str] = ContextVar("tavily_api_key")


def _get_env_api_key() -> str:
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        raise RuntimeError(
            "Tavily API key not found. Set TAVILY_API_KEY env var "
            "or provide 'x-auth-token' header to the server."
        )
    return key


def get_tavily_api_key() -> str:
    """Get the Tavily API key for the current request (ContextVar → env)."""
    try:
        return tavily_api_key_context.get()
    except LookupError:
        return _get_env_api_key()


def get_tavily_client() -> TavilyClient:
    """Create a TavilyClient bound to the current request's API key."""
    api_key = get_tavily_api_key()
    return TavilyClient(api_key=api_key)
