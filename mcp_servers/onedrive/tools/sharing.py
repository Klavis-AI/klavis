import httpx
import logging
from typing import Tuple, Union, Dict, Any, Literal
from .base import get_onedrive_client

# Configure logging
logger = logging.getLogger(__name__)

async def onedrive_list_shared_items() -> Union[Tuple[str, Dict[str, Any]], Tuple[str, int, str]]:
    """
    List all items shared with the current user in OneDrive.

    Returns:
    - On success: Tuple with status message and dictionary containing shared items
    - On failure: Tuple with error message and details (status code and response text)
    """
    client = get_onedrive_client()
    if not client:
        logger.error("Failed to initialize OneDrive client")
        return ("Could not get OneDrive client",)

    url = f"{client['base_url']}/me/drive/sharedWithMe"

    try:
        logger.info("Requesting list of shared items")
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=client['headers'])
        if response.ok:
            items = response.json()
            item_count = len(items.get('value', []))
            logger.info(f"Successfully retrieved {item_count} shared items")
            return ("Items shared with me:", items)
        else:
            logger.error(f"Failed to get shared items. Status: {response.status_code}, Response: {response.text}")
            return ("Error:", response.status_code, response.text)
    except Exception as e:
        logger.error(f"Exception while fetching shared items: {str(e)}")
        return ("Error:", str(e))
