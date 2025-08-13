import logging
from typing import Optional
from .base import run_stripe_tool

# Configure logging
logger = logging.getLogger(__name__)

async def create_product(name: str, description: Optional[str] = None) -> str:
    """Create a product in Stripe."""
    try:
        return run_stripe_tool("create_product", {"name": name, "description": description})
    except Exception as e:
        logger.exception(f"Error creating product: {e}")
        raise

async def list_products(limit: Optional[int] = None) -> str:
    """Fetch a list of products from Stripe."""
    try:
        return run_stripe_tool("list_products", {"limit": limit})
    except Exception as e:
        logger.exception(f"Error listing products: {e}")
        raise

async def create_price(product: str, unit_amount: int, currency: str) -> str:
    """Create a price for a product in Stripe."""
    try:
        return run_stripe_tool("create_price", {
            "product": product, 
            "unit_amount": unit_amount, 
            "currency": currency
        })
    except Exception as e:
        logger.exception(f"Error creating price: {e}")
        raise

async def list_prices(product: Optional[str] = None, limit: Optional[int] = None) -> str:
    """Fetch a list of prices from Stripe."""
    try:
        return run_stripe_tool("list_prices", {"product": product, "limit": limit})
    except Exception as e:
        logger.exception(f"Error listing prices: {e}")
        raise 