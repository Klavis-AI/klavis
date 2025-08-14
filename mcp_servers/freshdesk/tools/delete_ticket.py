import logging
from typing import Any, Dict

from .base import get_freshdesk_client, FreshdeskToolExecutionError

logger = logging.getLogger(__name__)


async def delete_ticket(ticket_id: int) -> Dict[str, Any]:
    # Input validation
    if not ticket_id or ticket_id <= 0:
        raise FreshdeskToolExecutionError(
            "Valid ticket ID is required",
            f"Invalid ticket ID: {ticket_id}"
        )
    
    client = get_freshdesk_client()
    
    try:
        result = await client.delete(f"/tickets/{ticket_id}")
        logger.info(f"Successfully deleted ticket {ticket_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to delete ticket {ticket_id}: {str(e)}")
        raise
