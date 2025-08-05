import httpx
import logging
from typing import Tuple, Union, Dict, List, Any
from .base import get_onedrive_client

# Configure logging
logger = logging.getLogger(__name__)

async def onedrive_list_root_files_folders() -> Union[Tuple[str, Dict[str, Any]], Tuple[str, int, str]]:
    """
    List all files and folders in the root of OneDrive.

    Returns:
    - On success: Tuple with status message and dictionary containing items
    - On failure: Tuple with error message and details
    """
    client = get_onedrive_client()
    if not client:
        logger.error("Could not get OneDrive client")
        return "Could not get OneDrive client"

    url = f"{client['base_url']}/me/drive/root/children"

    try:
        logger.info("Listing files and folders in root directory")
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.get(url, headers=client['headers'])
            return "Files:", response.json()
    except Exception as e:
        logger.error(f"Exception while listing root items: {e}")
        return "Error:", str(e)

async def onedrive_list_inside_folder(folder_id: str) -> Union[Tuple[str, Dict[str, Any]], Tuple[str, int, str]]:
    """
    List all items inside a specific folder.

    Parameters:
    - folder_id: The ID of the folder to list contents from

    Returns:
    - On success: Tuple with status message and dictionary containing items
    - On failure: Tuple with error message and details
    """
    client = get_onedrive_client()
    if not client:
        logger.error("Could not get OneDrive client")
        return "Could not get OneDrive client"

    url = f"{client['base_url']}/me/drive/items/{folder_id}/children"

    try:
        logger.info(f"Listing items inside folder ID: {folder_id}")
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.get(url, headers=client['headers'])
            return "Items inside folder:", response.json()
    except Exception as e:
        logger.error(f"Exception while listing folder items: {e}")
        return "Error:", str(e)

async def onedrive_search_item_by_name(itemname: str) -> Union[Tuple[str, Dict[str, Any]], Tuple[str, int, str]]:
    """
    Search for items by name in OneDrive.

    Parameters:
    - itemname: The name or partial name of the item to search for

    Returns:
    - On success: Tuple with status message and dictionary containing search results
    - On failure: Tuple with error message and details
    """
    client = get_onedrive_client()
    if not client:
        logger.error("Could not get OneDrive client")
        return "Could not get OneDrive client"

    url = f"{client['base_url']}/me/drive/root/search(q='{itemname}')"

    try:
        logger.info(f"Searching for items with name: {itemname}")
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.get(url, headers=client['headers'])
            return "Found items:", response.json()
    except Exception as e:
        logger.error(f"Exception while searching items: {e}")
        return "Error:", str(e)

async def onedrive_search_folder_by_name(folder_name: str) -> Union[Tuple[str, List[Dict[str, Any]]], Tuple[str, int, str]]:
    """
    Search for folders by name in OneDrive.

    Parameters:
    - folder_name: The name or partial name of the folder to search for

    Returns:
    - On success: Tuple with status message and list of matching folders
    - On failure: Tuple with error message and details
    """
    client = get_onedrive_client()
    if not client:
        logger.error("Could not get OneDrive client")
        return "Could not get OneDrive client"

    url = f"{client['base_url']}/me/drive/root/search(q='{folder_name}')"

    try:
        logger.info(f"Searching for folders with name: {folder_name}")
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.get(url, headers=client['headers'])
            data = response.json()
            folders = [item for item in data.get('value', []) if 'folder' in item]
            return "Found folders:", folders

    except Exception as e:
        logger.error(f"Exception while searching folders: {e}")
        return "Error:", str(e)

async def onedrive_get_item_by_id(item_id: str) -> Union[Dict[str, Any], Tuple[str, int, str]]:
    """
    Get item details by its ID.

    Parameters:
    - item_id: The ID of the item to retrieve

    Returns:
    - On success: Dictionary containing item details
    - On failure: Tuple with error message and details
    """
    client = get_onedrive_client()
    if not client:
        logger.error("Could not get OneDrive client")
        return "Could not get OneDrive client"

    url = f"{client['base_url']}/me/drive/items/{item_id}"

    try:
        logger.info(f"Getting item with ID: {item_id}")
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.get(url, headers=client['headers'])
            data = response.json()
            logger.info(f"Successfully retrieved item: {data.get('name', 'unknown')}")
            return data
    except Exception as e:
        logger.error(f"Exception while getting item: {e}")
        return "Error:", str(e)