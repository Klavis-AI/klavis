import logging
from typing import Optional
from .base import run_stripe_tool

# Configure logging
logger = logging.getLogger(__name__)

async def list_invoices(customer: Optional[str] = None, limit: Optional[int] = None) -> str:
    """List invoices in Stripe."""
    try:
        return run_stripe_tool("list_invoices", {"customer": customer, "limit": limit})
    except Exception as e:
        logger.exception(f"Error listing invoices: {e}")
        raise

async def create_invoice(customer: str, days_until_due: Optional[int] = None) -> str:
    """Create an invoice in Stripe.""" 
    try:
        return run_stripe_tool("create_invoice", {"customer": customer, "days_until_due": days_until_due})
    except Exception as e:
        logger.exception(f"Error creating invoice: {e}")
        raise

async def create_invoice_item(customer: str, price: str, invoice: str) -> str:
    """Create an invoice item in Stripe."""
    try:
        return run_stripe_tool("create_invoice_item", {
            "customer": customer, 
            "price": price, 
            "invoice": invoice
        })
    except Exception as e:
        logger.exception(f"Error creating invoice item: {e}")
        raise

async def finalize_invoice(invoice: str) -> str:
    """Finalize an invoice in Stripe."""
    try:
        return run_stripe_tool("finalize_invoice", {"invoice": invoice})
    except Exception as e:
        logger.exception(f"Error finalizing invoice: {e}")
        raise 