import httpx
import logging
from .base import get_outlookMail_client
import base64
import os

# Configure logging
logger = logging.getLogger(__name__)

async def outlookMail_get_attachment_details(
        message_id: str,
        attachment_id: str,
        expand: str = None
) -> dict:
    """
    Get a specific attachment from an Outlook mail message.

    Args:
        message_id (str): ID of the message that has the attachment.
        attachment_id (str): ID of the attachment to retrieve.
        expand (str, optional):
            An OData $expand expression to include related entities.
            Example: "microsoft.graph.itemattachment/item" to expand item attachments.

    Returns:
        dict: JSON response from Microsoft Graph API with attachment details,
              or an error message if the request fails.

    Notes:
        - Requires an authenticated Outlook client.
        - This function sends a GET request to:
          https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments/{attachment_id}
          and adds $expand if provided.
    """
    client = get_outlookMail_client()  # same client you’re using for other outlook calls
    if not client:
        logger.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/messages/{message_id}/attachments/{attachment_id}"

    params = {}
    if expand:
        params['$expand'] = expand

    try:
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.get(url, headers=client['headers'], params=params)
            return response.json()
    except Exception as e:
        logger.error(f"Could not get Outlook attachment at {url}: {e}")
        return {"error": f"Could not get Outlook attachment at {url}"}

async def outlookMail_list_attachments(message_id: str) -> dict:
    """
    List attachments from an Outlook mail message.

    Args:
        message_id (str): The ID of the message to list attachments from.

    Returns:
        dict: JSON response from Microsoft Graph API with the list of attachments,
              or an error message if the request fails.
    """
    client = get_outlookMail_client()  # same client used for other Outlook calls
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/messages/{message_id}/attachments"

    try:
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.get(url, headers=client['headers'])
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logging.error(f"Could not list attachments at {url}: {e}")
        return {"error": f"Could not list attachments at {url}: {e}"}