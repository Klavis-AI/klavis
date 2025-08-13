import logging
from typing import Optional
from .base import run_stripe_tool

# Configure logging
logger = logging.getLogger(__name__)

async def create_customer(name: str, email: Optional[str] = None) -> str:
    """Create a customer in Stripe."""
    try:
        return run_stripe_tool("create_customer", {"name": name, "email": email})
    except Exception as e:
        logger.exception(f"Error creating customer: {e}")
        raise

async def list_customers(limit: Optional[int] = None, email: Optional[str] = None) -> str:
    """Fetch a list of customers from Stripe."""
    try:
        return run_stripe_tool("list_customers", {"limit": limit, "email": email})
    except Exception as e:
        logger.exception(f"Error listing customers: {e}")
        raise 