import requests
import logging
from .base import get_onedrive_client

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
    client = get_onedrive_client()
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders"
    params = {}
    if include_hidden:
        params["includeHiddenFolders"] = "true"

    try:
        response = requests.get(url, headers=client['headers'], params=params)
        response.raise_for_status()
        logging.info("Fetched mail folders")
        return response.json()
    except Exception as e:
        logging.error(f"Could not get mail folders from {url}: {e}")
        return {"error": f"Could not get mail folders from {url}: {e}"}

async def outlookMail_get_mail_folder(folder_id: str) -> dict:
    """
    Get details of a specific mail folder by its ID.

    Args:
        folder_id (str): The unique ID of the mail folder.

    Returns:
        dict: JSON response from Microsoft Graph with folder details,
              or error info if request fails.
    """
    client = get_onedrive_client()
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders/{folder_id}"

    try:
        response = requests.get(url, headers=client['headers'])
        response.raise_for_status()
        logging.info(f"Retrieved mail folder {folder_id}")
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
    client = get_onedrive_client()
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders"
    payload = {
        "displayName": display_name,
        "isHidden": is_hidden
    }

    try:
        response = requests.post(url, headers=client['headers'], json=payload)
        response.raise_for_status()
        logging.info(f"Created mail folder: {display_name}")
        return response.json()
    except Exception as e:
        logging.error(f"Could not create mail folder at {url}: {e}")
        return {"error": f"Could not create mail folder at {url}"}

async def outlookMail_list_child_folders(
        folder_id: str,
        include_hidden: bool = False
) -> dict:
    """
    List child folders of a specific Outlook mail folder.

    Args:
        folder_id (str): ID of the parent folder.
        include_hidden (bool, optional): Whether to include hidden folders. Defaults to False.

    Returns:
        dict: JSON response from Microsoft Graph with the list of child folders,
              or error info if request fails.
    """
    client = get_onedrive_client()
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders/{folder_id}/childFolders"
    params = {}
    if include_hidden:
        params['includeHiddenFolders'] = 'true'

    try:
        response = requests.get(url, headers=client['headers'], params=params)
        response.raise_for_status()
        logging.info(f"Retrieved child folders of folder: {folder_id}")
        return response.json()
    except Exception as e:
        logging.error(f"Could not get child folders from {url}: {e}")
        return {"error": f"Could not get child folders from {url}"}

async def outlookMail_create_child_folder(
        parent_folder_id: str,
        display_name: str,
        is_hidden: bool = False
) -> dict:
    """
    Create a child mail folder inside a specified Outlook parent folder.

    Args:
        parent_folder_id (str): ID of the parent mail folder.
        display_name (str): Display name for the new folder.
        is_hidden (bool, optional): Whether the new folder should be hidden. Defaults to False.

    Returns:
        dict: Created folder details on success, or error message.
    """
    client = get_onedrive_client()
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders/{parent_folder_id}/childFolders"

    payload = {
        "displayName": display_name,
        "isHidden": is_hidden
    }

    try:
        response = requests.post(url, headers=client['headers'], json=payload)
        response.raise_for_status()
        logging.info(f"Created child folder '{display_name}' under folder: {parent_folder_id}")
        return response.json()
    except Exception as e:
        logging.error(f"Could not create child folder at {url}: {e}")
        return {"error": f"Could not create child folder at {url}"}



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
    client = get_onedrive_client()
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders/{folder_id}"
    payload = {"displayName": display_name}

    try:
        response = requests.patch(url, headers=client['headers'], json=payload)
        response.raise_for_status()
        logging.info(f"Updated folder {folder_id} display name to '{display_name}'")
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
    client = get_onedrive_client()
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders/{folder_id}"

    try:
        response = requests.delete(url, headers=client['headers'])
        if response.status_code == 204:
            logging.info(f"Deleted folder with ID {folder_id}")
            return {"message": f"Folder {folder_id} deleted successfully"}
        else:
            logging.error(f"Failed to delete folder {folder_id}: {response.text}")
            return {"error": f"Unexpected response: {response.status_code}", "details": response.text}
    except Exception as e:
        logging.error(f"Could not delete folder at {url}: {e}")
        return {"error": f"Could not delete folder at {url}"}

async def outlookMail_copy_folder(
        folder_id: str,
        destination_id: str
) -> dict:
    """
    Copy an Outlook mail folder to another destination folder.

    Args:
        folder_id (str): ID of the folder you want to copy.
        destination_id (str): ID of the destination folder.

    Returns:
        dict: Response from Microsoft Graph API or error info.
    """
    client = get_onedrive_client()
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders/{folder_id}/copy"
    payload = {
        "destinationId": destination_id
    }

    try:
        response = requests.post(url, headers=client['headers'], json=payload)
        response.raise_for_status()
        logging.info(f"Copied folder {folder_id} to destination {destination_id}")
        return response.json()
    except Exception as e:
        logging.error(f"Could not copy Outlook folder at {url}: {e}")
        return {"error": f"Could not copy Outlook folder at {url}"}

async def outlookMail_get_folder_delta(max_pagesize: int = 2) -> dict:
    """
    Get changes (delta) for all mail folders in the signed-in user's mailbox.

    Args:
        max_pagesize (int, optional): Max number of items per page. Defaults to 2.

    Returns:
        dict: JSON response from Microsoft Graph API with folder delta,
              or error info on failure.
    """
    client = get_onedrive_client()
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders/delta"
    headers = client['headers'].copy()
    headers["Prefer"] = f"odata.maxpagesize={max_pagesize}"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        logging.info("Retrieved folder delta successfully")
        return response.json()
    except Exception as e:
        logging.error(f"Could not get folder delta from {url}: {e}")
        return {"error": f"Could not get folder delta from {url}"}

async def outlookMail_move_folder(
        folder_id: str,
        destination_id: str
) -> dict:
    """
    Move an Outlook mail folder to another folder.

    Args:
        folder_id (str): The ID of the folder you want to move.
        destination_id (str): The ID of the destination folder.

    Returns:
        dict: JSON response from Microsoft Graph API or an error dict.
    """
    client = get_onedrive_client()  # reuse your existing authenticated client
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders/{folder_id}/move"
    payload = {
        "destinationId": destination_id
    }

    try:
        response = requests.post(url, headers=client['headers'], json=payload)
        response.raise_for_status()
        logging.info("Moved Outlook mail folder")
        return response.json()
    except Exception as e:
        logging.error(f"Could not move Outlook mail folder at {url}: {e}")
        return {"error": f"Could not move Outlook mail folder at {url}"}


async def outlookMail_permanent_delete_folder(
        user_id: str,
        folder_id: str
) -> dict:
    """
    Permanently delete an Outlook mail folder for a user.

    Args:
        user_id (str): The user's ID or userPrincipalName (e.g., 'user@domain.com').
        folder_id (str): The ID of the folder to permanently delete.

    Returns:
        dict: API response or error message.
    """
    client = get_onedrive_client()  # your usual way to get Graph auth headers
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}


    url = f"{client['base_url']}/users/{user_id}/mailFolders/{folder_id}/permanentDelete"

    try:
        response = requests.post(url, headers=client['headers'])
        response.raise_for_status()
        logging.info(f"Permanently deleted folder: {folder_id}")
        return {"success": True}
    except Exception as e:
        logging.error(f"Could not permanently delete folder at {url}: {e}")
        return {"error": str(e)}