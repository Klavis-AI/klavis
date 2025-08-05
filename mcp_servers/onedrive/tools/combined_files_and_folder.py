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
        return "Could not get OneDrive client"

    url = f"{client['base_url']}/me/drive/items/{file_id}"
    data = {"name": new_name}

    try:
        logger.info(f"Renaming item {file_id} to {new_name}")

        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.patch(
                url,
                headers={ **client['headers'], "Content-Type": "application/json"},
                json=data
            )
            return "Renamed successfully:", response.json()
    except Exception as e:
        logger.error(f"Exception occurred while renaming item: {e}")
        return "Error:", str(e)


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
        return "Could not get OneDrive client"

    url = f"{client['base_url']}/me/drive/items/{item_id}"
    body = {
        "parentReference": {"id": new_parent_id}
    }

    try:
        logger.info(f"Moving item {item_id} to parent {new_parent_id}")
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.patch(url, headers=client['headers'], json=body)
            return "Item moved:", response.json()
    except Exception as e:
        logger.error(f"Exception occurred while moving item: {e}")
        return ("Error:", str(e))


async def onedrive_delete_item(item_id: str) -> Union[Tuple[str], Tuple[str, int, str]]:
    """
    Deletes an item from OneDrive.

    Args:
        item_id: ID of the item to delete.

    Returns:
        A tuple with a success message OR an error message with details.
    """
    client = get_onedrive_client()
    if not client:
        logger.error("Could not get OneDrive client")
        return "Could not get OneDrive client", 500, "Authentication client not found."

    url = f"{client['base_url']}/me/drive/items/{item_id}"

    try:
        logger.info(f"Deleting item {item_id}")
        # Although creating a client for each call is inefficient, this works
        # as a self-contained function.
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.delete(url, headers=client['headers'])

            # Key Fix: Check the status code from the response.
            # A successful delete operation returns 204 No Content.
            if response.status_code == 204:
                return "Deleted successfully"
            else:
                # If it's not 204, the API returned an error.
                logger.error(f"Error deleting item {item_id}: {response.status_code} - {response.text}")
                # Attempt to return the JSON error from the API, falling back to raw text.
                try:
                    error_details = response.json()
                except Exception:
                    error_details = response.text
                return "Error:", response.status_code, str(error_details)

    except httpx.RequestError as exc:
        # This handles network-level errors (e.g., cannot connect).
        logger.error(f"Network error while deleting item {item_id}: {exc}")
        return "Error:", 503, f"A network error occurred: {exc}"
    except Exception as exc:
        # This handles any other unexpected errors.
        logger.error(f"An unexpected exception occurred while deleting item: {exc}")
        return "Error:", 500, f"An unexpected error occurred: {exc}"
