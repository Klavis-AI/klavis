import logging
from typing import Tuple, Union, Dict, Any
from .base import get_onedrive_client

# Configure logging
logger = logging.getLogger(__name__)

async def onedrive_create_folder(
    parent_folder_id: str,
    new_folder_name: str,
    behavior: str = "fail"
) -> Union[Tuple[str, Dict[str, Any]], Tuple[str, int, str]]:
    """
    Create a new folder in a specific OneDrive parent folder.

    Parameters:
    - parent_folder_id: ID of the parent folder where the new folder will be created
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
        return ("Could not get OneDrive client",)

    url = f"{client['base_url']}/me/drive/items/{parent_folder_id}/children"
    data = {
        "name": new_folder_name,
        "folder": {},
        "@microsoft.graph.conflictBehavior": behavior
    }

    try:
        logger.info(f"Creating folder '{new_folder_name}' in parent {parent_folder_id} with behavior={behavior}")
        response = requests.post(
            url,
            headers={**client['headers'], "Content-Type": "application/json"},
            json=data
        )

        if response.ok:
            logger.info(f"Successfully created folder '{new_folder_name}' in {parent_folder_id}")
            return ("Folder created successfully:", response.json())
        else:
            logger.error(f"Failed to create folder: {response.status_code} - {response.text}")
            return ("Error:", response.status_code, response.text)
    except Exception as e:
        logger.error(f"Exception occurred while creating folder: {e}")
        return ("Error:", str(e))

async def onedrive_create_folder_in_root(
    folder_name: str
) -> Union[Dict[str, Any], Tuple[str, int, str]]:
    """
    Create a new folder in the root of OneDrive.

    Parameters:
    - folder_name: Name for the new folder
    Note: Automatically uses "rename" behavior for conflict resolution

    Returns:
    - On success: Folder creation response JSON
    - On failure: Tuple with error message and details
    """
    client = get_onedrive_client()
    if not client:
        logger.error("Could not get OneDrive client")
        return ("Could not get OneDrive client",)

    url = f"{client['base_url']}/me/drive/root/children"
    body = {
        "name": folder_name,
        "folder": {},
        "@microsoft.graph.conflictBehavior": "rename"
    }

    try:
        logger.info(f"Creating folder '{folder_name}' in root directory")
        response = requests.post(
            url,
            headers=client['headers'],
            json=body
        )

        if response.ok:
            logger.info(f"Successfully created folder '{folder_name}' in root")
            return response.json()
        else:
            logger.error(f"Failed to create folder in root: {response.status_code} - {response.text}")
            return ("Error creating folder:", response.status_code, response.text)
    except Exception as e:
        logger.error(f"Exception occurred while creating folder in root: {e}")
        return ("Error:", str(e))