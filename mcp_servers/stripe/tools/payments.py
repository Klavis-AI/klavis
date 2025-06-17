import logging
from typing import Optional
from .base import run_stripe_tool

# Configure logging
logger = logging.getLogger(__name__)

async def create_payment_link(price: str, quantity: int) -> str:
    """Create a payment link in Stripe."""
    try:
        return run_stripe_tool("create_payment_link", {"price": price, "quantity": quantity})
    except Exception as e:
        logger.exception(f"Error creating payment link: {e}")
        raise

async def list_payment_intents(customer: Optional[str] = None, limit: Optional[int] = None) -> str:
    """List payment intents in Stripe."""
    try:
        return run_stripe_tool("list_payment_intents", {"customer": customer, "limit": limit})
    except Exception as e:
        logger.exception(f"Error listing payment intents: {e}")
        raise

async def create_refund(payment_intent: str, amount: Optional[int] = None) -> str:
    """Refund a payment intent in Stripe."""
    try:
        return run_stripe_tool("create_refund", {"payment_intent": payment_intent, "amount": amount})
    except Exception as e:
        logger.exception(f"Error creating refund: {e}")
        raise 