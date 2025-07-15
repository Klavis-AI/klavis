import requests
import logging
from .base import get_onedrive_client

# Configure logging
logger = logging.getLogger(__name__)

async def outlookMail_update_inference_override(
        override_id: str,
        classify_as: str = "focused"
) -> dict:
    """
    Update an existing inference classification override.

    Args:
        override_id (str): The ID of the override to update.
        classify_as (str): "focused" or "other".

    Returns:
        dict: JSON response from Microsoft Graph API, or an error message.
    """
    client = get_onedrive_client()  # your function to get the authenticated client
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/inferenceClassification/overrides/{override_id}"
    payload = {
        "classifyAs": classify_as
    }

    try:
        response = requests.patch(url, headers=client['headers'], json=payload)
        response.raise_for_status()
        logging.info("Updated inference classification override")
        return response.json()
    except Exception as e:
        logging.error(f"Could not update inference classification override at {url}: {e}")
        return {"error": f"Could not update inference classification override at {url}"}

async def outlookMail_delete_inference_override(override_id: str) -> str:
    """
    Delete an inference classification override by ID.

    Args:
        override_id (str): The ID of the override to delete.

    Returns:
        str: "Deleted" on success, or an error message.
    """
    client = get_onedrive_client()  # your helper to get the authenticated client
    if not client:
        logging.error("Could not get Outlook client")
        return "Could not get Outlook client"

    url = f"{client['base_url']}/me/inferenceClassification/overrides/{override_id}"

    try:
        response = requests.delete(url, headers=client['headers'])
        if response.status_code == 204:
            logging.info("Deleted inference classification override")
            return "Deleted"
        else:
            try:
                return response.json()
            except Exception:
                return f"Unexpected response: {response.status_code}"
    except Exception as e:
        logging.error(f"Could not delete inference classification override at {url}: {e}")
        return f"Error: {e}"

async def outlookMail_list_inference_overrides() -> dict:
    """
    List all Focused Inbox overrides (inferenceClassification overrides)
    for the signed-in user.

    Returns:
        dict: JSON response from Microsoft Graph API containing the list of overrides,
              or an error message if the request fails.
    """
    client = get_onedrive_client()  # same client you use for other Outlook calls
    if not client:
        logger.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/inferenceClassification/overrides"

    try:
        response = requests.get(url, headers=client['headers'])
        response.raise_for_status()
        logger.info("Fetched Focused Inbox overrides")
        return response.json()  # contains list of overrides; each has an 'id'
    except Exception as e:
        logger.error(f"Could not list overrides from {url}: {e}")
        return {"error": f"Could not list overrides from {url}"}

