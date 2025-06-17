import logging
from .base import run_stripe_tool

# Configure logging
logger = logging.getLogger(__name__)

async def retrieve_balance() -> str:
    """Retrieve the balance from Stripe. It takes no input."""
    try:
        return run_stripe_tool("retrieve_balance", {})
    except Exception as e:
        logger.exception(f"Error retrieving balance: {e}")
        raise 