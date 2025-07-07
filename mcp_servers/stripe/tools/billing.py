import logging
from typing import Optional
from .base import run_stripe_tool

# Configure logging
logger = logging.getLogger(__name__)

async def create_billing_portal_session(customer: str, return_url: Optional[str] = None) -> str:
    """Create a billing portal session."""
    try:
        return run_stripe_tool("create_billing_portal_session", {
            "customer": customer, 
            "return_url": return_url
        })
    except Exception as e:
        logger.exception(f"Error creating billing portal session: {e}")
        raise 