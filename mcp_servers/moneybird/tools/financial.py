import logging
from typing import Any, Dict, Optional
from .base import make_request

# Configure logging
logger = logging.getLogger(__name__)

async def moneybird_list_financial_accounts(
    administration_id: str
) -> Dict[str, Any]:
    """List all financial accounts in Moneybird."""
    logger.info("Executing tool: moneybird_list_financial_accounts")
    
    try:
        return await make_request("GET", administration_id, "/financial_accounts")
    except Exception as e:
        logger.exception(f"Error executing tool moneybird_list_financial_accounts: {e}")
        raise e

async def moneybird_list_products(
    administration_id: str,
    query: Optional[str] = None,
    page: Optional[int] = None
) -> Dict[str, Any]:
    """List all products in Moneybird."""
    logger.info("Executing tool: moneybird_list_products")
    
    params = {}
    if query:
        params["query"] = query
    if page:
        params["page"] = page
    
    try:
        return await make_request("GET", administration_id, "/products", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool moneybird_list_products: {e}")
        raise e