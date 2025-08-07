import httpx
import logging
from .base import get_outlookMail_client

# Configure logging
logger = logging.getLogger(__name__)

async def outlookMail_list_folders(include_hidden: bool = True) -> dict:
    """
    List mail folders in the signed-in user's mailbox.

    Args:
        include_hidden (bool, optional): Whether to include hidden folders. Defaults to True.

    Returns:
        dict: JSON response with list of folders or an error.
    """
    client = get_outlookMail_client()
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders"
    params = {}
    if include_hidden:
        params["includeHiddenFolders"] = "true"

    try:
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.get(url, headers=client['headers'], params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Could not get mail folders from {url}: {e}")
        return {"error": f"Could not get mail folders from {url}: {e}"}

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
    client = get_outlookMail_client()
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
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.get(url, headers=client['headers'], params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Could not get messages from {url}: {e}")
        return {"error": f"Could not get messages from {url}"}

async def outlookMail_get_mail_folder_details(folder_id: str) -> dict:
    """
    Get details of a specific mail folder by its ID.

    Args:
        folder_id (str): The unique ID of the mail folder.

    Returns:
        dict: JSON response from Microsoft Graph with folder details,
              or error info if request fails.
    """
    client = get_outlookMail_client()
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders/{folder_id}"

    try:
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.get(url, headers=client['headers'])
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logging.error(f"Could not get mail folder at {url}: {e}")
        return {"error": f"Could not get mail folder at {url}"}

async def outlookMail_create_mail_folder(
        display_name: str,
        is_hidden: bool = False
) -> dict:
    """
    Create a new mail folder in the signed-in user's mailbox.

    Args:
        display_name (str): The name of the new folder.
        is_hidden (bool, optional): Whether the folder is hidden. Defaults to False.

    Returns:
        dict: JSON response from Microsoft Graph with the created folder info,
              or error info if request fails.
    """
    client = get_outlookMail_client()
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders"
    payload = {
        "displayName": display_name,
        "isHidden": is_hidden
    }

    try:
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.post(url, headers=client['headers'], json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logging.error(f"Could not create mail folder at {url}: {e}")
        return {"error": f"Could not create mail folder at {url}"}

async def outlookMail_update_folder_display_name(
        folder_id: str,
        display_name: str
) -> dict:
    """
    Update the display name of an Outlook mail folder.

    Args:
        folder_id (str): ID of the mail folder to update.
        display_name (str): New display name.

    Returns:
        dict: JSON response on success, or error details.
    """
    client = get_outlookMail_client()
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders/{folder_id}"
    payload = {"displayName": display_name}

    try:
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.patch(url, headers=client['headers'], json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logging.error(f"Failed to update folder at {url}: {e}")
        return {"error": f"Failed to update folder at {url}"}

async def outlookMail_delete_folder(folder_id: str) -> dict:
    """
    Delete an Outlook mail folder by ID.

    Args:
        folder_id (str): The ID of the folder to delete.

    Returns:
        dict: Result message or error details.
    """
    client = get_outlookMail_client()
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders/{folder_id}"

    try:
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.delete(url, headers=client['headers'])
        if response.status_code == 204:
            logging.info(f"Deleted folder with ID {folder_id}")
            return {"message": f"Folder {folder_id} deleted successfully"}
        else:
            logging.error(f"Failed to delete folder {folder_id}: {response.text}")
            return {"error": f"Unexpected response: {response.status_code}", "details": response.text}
    except Exception as e:
        logging.error(f"Could not delete folder at {url}: {e}")
        return {"error": f"Could not delete folder at {url}"}
