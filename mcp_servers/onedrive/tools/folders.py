import httpx
import logging
from typing import Tuple, Union, Dict, Any
from .base import get_onedrive_client

# Configure logging
logger = logging.getLogger(__name__)

async def onedrive_create_folder(
    parent_folder: str,
    new_folder_name: str,
    behavior: str = "fail"
) -> Union[Tuple[str, Dict[str, Any]], Tuple[str, int, str]]:
    """
    Create a new folder in a specific OneDrive parent folder.

    Parameters:
    - parent_folder: 'root' to create in root or ID of the parent folder
    - new_folder_name: Name for the new folder
    - behavior: Conflict resolution behavior ("fail", "replace", or "rename")
               Default is "fail" (return error if folder exists)

    Returns:
    - On success: Tuple with success message and folder creation response JSON
    - On failure: Tuple with error message and details
    """
    client = get_onedrive_client()
    if not client:
        logger.error("Could not get OneDrive client")
        return "Could not get OneDrive client"

    url = f"{client['base_url']}/me/drive/items/{parent_folder}/children"
    data = {
        "name": new_folder_name,
        "folder": {},
        "@microsoft.graph.conflictBehavior": behavior
    }

    try:
        logger.info(f"Creating folder '{new_folder_name}' in parent {parent_folder} with behavior={behavior}")
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.post(
                url,
                headers={**client['headers'], "Content-Type": "application/json"},
                json=data
            )
            return "Folder created successfully:", response.json()
    except Exception as e:
        logger.error(f"Exception occurred while creating folder: {e}")
        return "Error:", str(e)