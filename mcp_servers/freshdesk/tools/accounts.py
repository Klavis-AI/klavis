from typing import Dict, List, Optional, Any
from .base import make_freshdesk_request, handle_freshdesk_error, remove_none_values
import logging

logger = logging.getLogger(__name__)


async def get_current_account() -> Dict[str, Any]:
    """
    Retrieve the current account.
    
    Returns:
        Dict containing the account data or error information
    """
    try:
        return await make_freshdesk_request("GET", "/account")
    except Exception as e:
        return handle_freshdesk_error(e, "retrieve", "current account")
    