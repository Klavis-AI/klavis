import requests
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
        response = requests.post(url, headers=client['headers'], json=payload)
        response.raise_for_status()
        logging.info(f"Created search folder: {display_name}")
        return response.json()
    except Exception as e:
        logging.error(f"Could not create search folder at {url}: {e}")
        return {"error": f"Could not create search folder at {url}"}


async def outlookMail_get_mail_search_folder(folder_id: str) -> dict:
    """
    Retrieve details of a specific Outlook mail folder by its ID.

    Args:
        folder_id (str): The unique ID of the mail folder.

    Returns:
        dict: JSON with folder details, or an error message.
    """
    client = get_onedrive_client()
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders/{folder_id}"

    try:
        response = requests.get(url, headers=client['headers'])
        response.raise_for_status()
        logging.info(f"Retrieved mail folder: {folder_id}")
        return response.json()
    except Exception as e:
        logging.error(f"Could not get mail folder from {url}: {e}")
        return {"error": f"Could not get mail folder from {url}"}

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
        response = requests.patch(url, headers=client['headers'], json=payload)
        response.raise_for_status()
        logging.info(f"Updated mail folder: {folder_id}")
        return response.json()
    except Exception as e:
        logging.error(f"Could not update mail folder at {url}: {e}")
        return {"error": f"Could not update mail folder at {url}"}
async def outlookMail_delete_mail_search_folder(folder_id: str) -> dict:
    """
    Delete a mail folder in Outlook by its folder ID.

    Args:
        folder_id (str): The unique ID of the mail folder to delete.

    Returns:
        dict: {"success": True} on success, or {"error": "..."} on failure.
    """
    client = get_onedrive_client()
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders/{folder_id}"

    try:
        response = requests.delete(url, headers=client['headers'])
        response.raise_for_status()
        logging.info(f"Deleted mail folder: {folder_id}")
        return {"success": True}
    except Exception as e:
        logging.error(f"Could not delete mail folder at {url}: {e}")
        return {"error": f"Could not delete mail folder at {url}"}

async def outlookMail_permanent_delete_mail_search_folder(folder_id: str) -> dict:
    """
    Permanently delete a mail folder in Outlook by its folder ID.

    Args:
        folder_id (str): The unique ID of the mail folder to permanently delete.

    Returns:
        dict: {"success": True} on success, or {"error": "..."} on failure.
    """
    client = get_onedrive_client()
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders/{folder_id}/permanentDelete"

    try:
        response = requests.post(url, headers=client['headers'])
        response.raise_for_status()
        logging.info(f"Permanently deleted mail folder: {folder_id}")
        return {"success": True}
    except Exception as e:
        logging.error(f"Could not permanently delete mail folder at {url}: {e}")
        return {"error": f"Could not permanently delete mail folder at {url}"}

async def outlookMail_get_messages_from_folder(
        folder_id: str,
        top: int = 10,
        filter_query: str = None,
        orderby: str = None,
        select: str = None
)-> dict:
    """
    Retrieve messages from a specific Outlook mail folder.

    Args:
        folder_id (str): The unique ID of the mail folder.
        top (int, optional): Max number of messages to return (default: 10).
        filter_query (str, optional): OData $filter expression (e.g., "contains(subject, 'weekly digest')").
        orderby (str, optional): OData $orderby expression (e.g., "receivedDateTime desc").
        select (str, optional): Comma-separated list of properties to include.

    Returns:
        dict: JSON response with list of messages, or error info.
    """
    client = get_onedrive_client()
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders/{folder_id}/messages"
    params = {'$top': top}

    if filter_query:
        params['$filter'] = filter_query
    if orderby:
        params['$orderby'] = orderby
    if select:
        params['$select'] = select

    try:
        response = requests.get(url, headers=client['headers'], params=params)
        response.raise_for_status()
        logging.info(f"Retrieved messages from folder {folder_id}")
        return response.json()
    except Exception as e:
        logging.error(f"Could not get messages from {url}: {e}")
        return {"error": f"Could not get messages from {url}"}
