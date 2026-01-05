import logging
from typing import Any, Dict

from .base import make_airtable_request, normalize_base

# Configure logging
logger = logging.getLogger("airtable_tools")


async def get_bases_info() -> Dict[str, Any]:
    """Get information about all bases."""
    endpoint = "meta/bases"
    logger.info("Executing tool: get_bases_info")
    raw_response = await make_airtable_request("GET", endpoint)
    
    bases = [normalize_base(b) for b in raw_response.get("bases", [])]
    return {
        "nextPageToken": raw_response.get("offset"),
        "count": len(bases),
        "bases": bases,
    }
