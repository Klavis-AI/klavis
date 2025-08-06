import httpx
import logging
from .base import get_onedrive_client

# Configure logging
logger = logging.getLogger(__name__)

async def outlookMail_create_mail_search_folder(
        parent_folder_id: str,
        display_name: str,
        include_nested_folders: bool,
        source_folder_ids: list,
        filter_query: str
) -> dict:
    """
    Create a new mail search folder under a specified parent folder.

    Args:
        parent_folder_id (str): ID of the parent mail folder.
        display_name (str): Display name for the search folder.
        include_nested_folders (bool): Whether to include subfolders.
        source_folder_ids (list): List of folder IDs to search.
        filter_query (str): OData filter query string (e.g., "contains(subject, 'weekly digest')").

    Returns:
        dict: Created search folder info on success, or error dict on failure.
    """

    client = get_onedrive_client()
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders/{parent_folder_id}/childFolders"

    payload = {
        "@odata.type": "microsoft.graph.mailSearchFolder",
        "displayName": display_name,
        "includeNestedFolders": include_nested_folders,
        "sourceFolderIds": source_folder_ids,
        "filterQuery": filter_query
    }

    try:
        async with httpx.AsyncClient() as httpx_client:
            response = httpx_client.post(url, headers=client['headers'], json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logging.error(f"Could not create search folder at {url}: {e}")
        return {"error": f"Could not create search folder at {url}"}

async def outlookMail_update_mail_search_folder(
        folder_id: str,
        displayName: str = None,
        includeNestedFolders: bool = None,
        sourceFolderIds: list = None,
        filterQuery: str = None
) -> dict:
    """
    Update a mail folder (typically a mailSearchFolder) in Outlook.

    Args:
        folder_id (str): The unique ID of the folder to update.
        displayName (str, optional): New display name for the folder.
        includeNestedFolders (bool, optional): Whether to do deep search (True) or shallow (False).
        sourceFolderIds (list of str, optional): IDs of folders to be mined.
        filterQuery (str, optional): OData filter to filter messages (e.g., "contains(subject, 'weekly digest')").

    Returns:
        dict: Updated folder object on success, or error info on failure.
    """
    client = get_onedrive_client()
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders/{folder_id}"

    payload = {}
    if displayName is not None:
        payload["displayName"] = displayName
    if includeNestedFolders is not None:
        payload["includeNestedFolders"] = includeNestedFolders
    if sourceFolderIds is not None:
        payload["sourceFolderIds"] = sourceFolderIds
    if filterQuery is not None:
        payload["filterQuery"] = filterQuery

    try:
        async with httpx.AsyncClient() as httpx_client:
            response = httpx_client.patch(url, headers=client['headers'], json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logging.error(f"Could not update mail folder at {url}: {e}")
        return {"error": f"Could not update mail folder at {url}"}
