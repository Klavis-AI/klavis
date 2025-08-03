import httpx
import logging
from typing import Tuple, Union
from .base import get_onedrive_client

# Configure logging
logger = logging.getLogger(__name__)


async def onedrive_rename_item(file_id: str, new_name: str) -> Union[Tuple[str, dict], Tuple[str, int, str]]:
    """
    Rename an item in OneDrive.

    Parameters:
    - file_id: ID of the file/item to rename
    - new_name: New name for the item

    Returns:
    - Tuple with success message and response data OR error message and details
    """
    client = get_onedrive_client()
    if not client:
        logger.error("Could not get OneDrive client")
        return ("Could not get OneDrive client",)

    url = f"{client['base_url']}/me/drive/items/{file_id}"
    data = {"name": new_name}

    try:
        logger.info(f"Renaming item {file_id} to {new_name}")

        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url,
                headers={ **client['headers'], "Content-Type": "application/json"},
                json=data
            )

        if response.ok:
            logger.info(f"Successfully renamed item {file_id}")
            return ("Renamed successfully:", response.json())
        else:
            logger.error(f"Error renaming item {file_id}: {response.status_code} - {response.text}")
            return ("Error:", response.status_code, response.text)
    except Exception as e:
        logger.error(f"Exception occurred while renaming item: {e}")
        return ("Error:", str(e))


async def onedrive_move_item(item_id: str, new_parent_id: str) -> Union[Tuple[str, dict], Tuple[str, int, str]]:
    """
    Move an item to a different folder in OneDrive.

    Parameters:
    - item_id: ID of the item to move
    - new_parent_id: ID of the destination folder

    Returns:
    - Tuple with success message and response data OR error message and details
    """
    client = get_onedrive_client()
    if not client:
        logger.error("Could not get OneDrive client")
        return ("Could not get OneDrive client",)

    url = f"{client['base_url']}/me/drive/items/{item_id}"
    body = {
        "parentReference": {"id": new_parent_id}
    }

    try:
        logger.info(f"Moving item {item_id} to parent {new_parent_id}")
        async with httpx.AsyncClient() as client:
            response = await client.patch(url, headers=client['headers'], json=body)

        if response.ok:
            logger.info(f"Successfully moved item {item_id}")
            return ("Item moved:", response.json())
        else:
            logger.error(f"Error moving item {item_id}: {response.status_code} - {response.text}")
            return ("Error:", response.status_code, response.text)
    except Exception as e:
        logger.error(f"Exception occurred while moving item: {e}")
        return ("Error:", str(e))


async def onedrive_delete_item(item_id: str) -> Union[Tuple[str], Tuple[str, int, str]]:
    """
    Delete an item from OneDrive.

    Parameters:
    - item_id: ID of the item to delete

    Returns:
    - Tuple with success message OR error message and details
    """
    client = get_onedrive_client()
    if not client:
        logger.error("Could not get OneDrive client")
        return ("Could not get OneDrive client",)

    url = f"{client['base_url']}/me/drive/items/{item_id}"

    try:
        logger.info(f"Deleting item {item_id}")
        async with httpx.AsyncClient() as client:
            response = await client.delete(url, headers=client['headers'])

        if response.status_code == 204:
            logger.info(f"Successfully deleted item {item_id}")
            return (f"Item {item_id} deleted.",)
        else:
            logger.error(f"Error deleting item {item_id}: {response.status_code} - {response.text}")
            return ("Error:", response.status_code, response.text)
    except Exception as e:
        logger.error(f"Exception occurred while deleting item: {e}")
        return ("Error:", str(e))