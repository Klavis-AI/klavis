import logging
from typing import Any, Dict, List
from .base import make_linkedin_request

# Configure logging
logger = logging.getLogger(__name__)

async def search_people(keywords: str, count: int = 10) -> List[Dict[str, Any]]:
    """Search for people on LinkedIn (Note: LinkedIn has restricted search APIs)."""
    logger.info(f"Executing tool: search_people with keywords: {keywords}")
    try:
        # Note: LinkedIn's people search API is heavily restricted and may not be available
        # with standard access tokens. This function may return limited results or errors.
        return [{"info": f"LinkedIn people search is restricted. Searched for: {keywords}", "note": "This feature requires special LinkedIn partnership access."}]
    except Exception as e:
        logger.exception(f"Error executing tool search_people: {e}")
        raise e