import requests
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

    Example:
        >>> result = onedrive_list_shared_items()
        >>> if isinstance(result, tuple) and result[0] == "Items shared with me:":
        >>>     shared_items = result[1]
    """
    client = get_onedrive_client()
    if not client:
        logger.error("Failed to initialize OneDrive client")
        return ("Could not get OneDrive client",)

    url = f"{client['base_url']}/me/drive/sharedWithMe"

    try:
        logger.info("Requesting list of shared items")
        response = requests.get(url, headers=client['headers'])

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

async def onedrive_create_share_link(
    item_id: str,
    link_type: Literal["view", "edit", "embed"] = "view",
    scope: Literal["anonymous", "organization"] = "anonymous"
) -> Union[Dict[str, Any], Tuple[str, int, str]]:
    """
    Create a sharing link for a OneDrive item.

    Parameters:
    - item_id: The ID of the item to share
    - link_type: Type of sharing link (view/edit/embed)
        - view: Read-only access
        - edit: Read-write access
        - embed: Embeddable link
    - scope: Audience for the link
        - anonymous: Anyone with the link
        - organization: Only people in your organization

    Returns:
    - On success: Dictionary containing sharing link information
    - On failure: Tuple with error message and details (status code and response text)

    Example:
        >>> link_info = onedrive_create_share_link("12345", "view", "anonymous")
        >>> if isinstance(link_info, dict):
        >>>     print(link_info['link']['webUrl'])
    """
    client = get_onedrive_client()
    if not client:
        logger.error("Failed to initialize OneDrive client")
        return ("Could not get OneDrive client",)

    if link_type not in ("view", "edit", "embed"):
        logger.error(f"Invalid link type specified: {link_type}")
        return ("Error:", 400, "Invalid link type. Must be 'view', 'edit', or 'embed'")

    url = f"{client['base_url']}/me/drive/items/{item_id}/createLink"
    data = {
        "type": link_type,
        "scope": scope
    }

    try:
        logger.info(f"Creating {link_type} share link for item {item_id} (scope: {scope})")
        response = requests.post(
            url,
            headers={**client['headers'], "Content-Type": "application/json"},
            json=data
        )

        if response.ok:
            result = response.json()
            logger.info(f"Successfully created share link for item {item_id}")
            logger.debug(f"Share link details: {result}")
            return result
        else:
            logger.error(f"Failed to create share link. Status: {response.status_code}, Response: {response.text}")
            return ("Error:", response.status_code, response.text)
    except Exception as e:
        logger.error(f"Exception while creating share link: {str(e)}")
        return ("Error:", str(e))