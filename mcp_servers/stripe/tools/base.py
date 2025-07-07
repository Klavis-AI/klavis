import logging
from typing import Any, Dict
from contextvars import ContextVar
from stripe_agent_toolkit.api import StripeAPI

# Configure logging
logger = logging.getLogger(__name__)

# Context variable to store the Stripe secret key for each request
stripe_secret_key_context: ContextVar[str] = ContextVar('stripe_secret_key')

def get_stripe_secret_key() -> str:
    """Get the Stripe secret key from context."""
    try:
        return stripe_secret_key_context.get()
    except LookupError:
        raise RuntimeError("Stripe secret key not found in request context")

def run_stripe_tool(method_name: str, params: dict) -> str:
    """
    Helper function that retrieves the Stripe secret key, initializes the API,
    and executes the specified method with the provided parameters.
    """
    api_key = get_stripe_secret_key()
    stripe_api = StripeAPI(secret_key=api_key, context=None)
    params = {k: v for k, v in params.items() if v is not None}
    return stripe_api.run(method_name, **params)  # type: ignore[no-any-return] 