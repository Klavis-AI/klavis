import logging
from typing import Any, Dict, Optional, List
from .base import make_request

# Configure logging
logger = logging.getLogger(__name__)

async def moneybird_list_sales_invoices(
    administration_id: str,
    state: Optional[str] = None,
    period: Optional[str] = None,
    contact_id: Optional[str] = None,
    created_after: Optional[str] = None,
    updated_after: Optional[str] = None,
    page: Optional[int] = None
) -> Dict[str, Any]:
    """List all sales invoices in Moneybird."""
    logger.info("Executing tool: moneybird_list_sales_invoices")
    
    params = {}
    if state:
        params["filter"] = f"state:{state}"
    if period:
        params["period"] = period
    if contact_id:
        params["contact_id"] = contact_id
    if created_after:
        params["created_after"] = created_after
    if updated_after:
        params["updated_after"] = updated_after
    if page:
        params["page"] = page
    
    try:
        return await make_request("GET", administration_id, "/sales_invoices", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool moneybird_list_sales_invoices: {e}")
        raise e

async def moneybird_get_sales_invoice(
    administration_id: str,
    invoice_id: str
) -> Dict[str, Any]:
    """Get details for a specific sales invoice by ID."""
    logger.info(f"Executing tool: moneybird_get_sales_invoice for invoice_id: {invoice_id}")
    
    try:
        return await make_request("GET", administration_id, f"/sales_invoices/{invoice_id}")
    except Exception as e:
        logger.exception(f"Error executing tool moneybird_get_sales_invoice: {e}")
        raise e

async def moneybird_create_sales_invoice(
    administration_id: str,
    invoice_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a new sales invoice in Moneybird."""
    logger.info("Executing tool: moneybird_create_sales_invoice")
    
    try:
        return await make_request("POST", administration_id, "/sales_invoices", data=invoice_data)
    except Exception as e:
        logger.exception(f"Error executing tool moneybird_create_sales_invoice: {e}")
        raise e