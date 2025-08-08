import httpx
import logging
from .base import get_outlookMail_client

# Configure logging
logger = logging.getLogger(__name__)

async def outlookMail_list_messages(
        top: int = 10,
        filter_query: str = None,
        orderby: str = None,
        select: str = None
) -> dict:
    """
    Retrieve a list of Outlook mail messages from the signed-in user's mailbox.

    Args:
        top (int, optional):
            The maximum number of messages to return. Defaults to 10.
        filter_query (str, optional):
            An OData $filter expression to filter messages by specific criteria.
            Example filters you can use:
                - "isRead eq false"                          → Only unread emails
                - "importance eq 'high'"                     → Emails marked as high importance
                - "from/emailAddress/address eq 'example@example.com'" → Emails sent by a specific address
                - "subject eq 'Welcome'"                      → Emails with a specific subject
                - "receivedDateTime ge 2025-07-01T00:00:00Z" → Emails received after a date
                - "hasAttachments eq true"                    → Emails that include attachments
                - Combine filters: "isRead eq false and importance eq 'high'"
        orderby (str, optional):
            An OData $orderby expression to sort results.
            Example: "receivedDateTime desc" (newest first)
        select (str, optional):
            Comma-separated list of fields to include in the response.
            Example: "subject,from,receivedDateTime"

    Returns:
        dict: JSON response from the Microsoft Graph API containing the list of messages
              or an error message if the request fails.

    Notes:
        - Requires an authenticated Outlook client.
        - This function internally builds the API request to:
          GET https://graph.microsoft.com/v1.0/me/messages
          with the provided query parameters.
    """

    client = get_outlookMail_client()
    if not client:
        logger.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}
    logger.info("Retrieving Outlook mail messages")

    url = f"{client['base_url']}/me/messages"
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
            return response.json()
    except Exception as e:
        logger.error(f"Could not get Outlook messages from {url}: {e}")
        return {"error": f"Could not get Outlook messages from {url}"}


async def outlookMail_list_messages_from_folder(
        folder_id: str,
        top: int = 10,
        filter_query: str = None,
        orderby: str = None,
        select: str = None
) -> dict:
    """
    Retrieve a list of Outlook mail messages from a specific folder in the signed-in user's mailbox.

    Args:
        folder_id (str):
            The unique ID of the Outlook mail folder to retrieve messages from.
            Example: 'AQMkADAwATNiZmYAZS05YmUxLTk3NDYtMDACLTAwCgAuAAAD...'
        top (int, optional):
            The maximum number of messages to return. Defaults to 10.
        filter_query (str, optional):
            An OData $filter expression to filter messages by specific criteria.
            Example filters you can use:
                - "isRead eq false"                          → Only unread emails
                - "importance eq 'high'"                     → Emails marked as high importance
                - "from/emailAddress/address eq 'example@example.com'" → Emails sent by a specific address
                - "subject eq 'Welcome'"                      → Emails with a specific subject
                - "receivedDateTime ge 2025-07-01T00:00:00Z" → Emails received after a date
                - "hasAttachments eq true"                    → Emails that include attachments
                - Combine filters: "isRead eq false and importance eq 'high'"
        orderby (str, optional):
            An OData $orderby expression to sort results.
            Example: "receivedDateTime desc" (newest first)
        select (str, optional):
            Comma-separated list of fields to include in the response.
            Example: "subject,from,receivedDateTime"

    Returns:
        dict: JSON response from the Microsoft Graph API containing the list of messages,
              or an error message if the request fails.

    Notes:
        - Requires an authenticated Outlook client.
        - This function sends a GET request to:
          https://graph.microsoft.com/v1.0/me/mailFolders/{folder_id}/messages
          with the provided query parameters.
    """

    client = get_outlookMail_client()
    if not client:
        logger.error("Could not get Outlook client")
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
            return response.json()
    except Exception as e:
        logger.error(f"Could not get Outlook messages from {url}: {e}")
        return {"error": f"Could not get Outlook messages from {url}"}

async def outlookMail_read_message(message_id: str) -> dict:
    """
    Get a specific Outlook mail message by its ID using Microsoft Graph API.

    Parameters:
    -----------
    message_id (str): The ID of the message to retrieve

    Returns:
    --------
    dict: The message object, or error on failure
    """
    url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}"
    client = get_outlookMail_client()
    if not client:
        logger.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}
    async with httpx.AsyncClient() as httpx_client:
        res = await httpx_client.get(url, headers=client['headers'])
        return res.json()


async def outlookMail_create_draft(
    subject: str,
    body_content: str,
    to_recipients: list,
    cc_recipients: list = None,
    bcc_recipients: list = None,
) -> dict:
    """
    Create a draft Outlook mail message using Microsoft Graph API (POST method)

    Required parameters:
    --------------------
    subject (str): Subject of the draft message
    body_content (str): HTML content of the message body
    to_recipients (list): List of email addresses for the "To" field

    Optional parameters:
    --------------------
    cc_recipients (list): List of email addresses for "Cc"
    bcc_recipients (list): List of email addresses for "Bcc"

    Returns:
    --------
    dict: Created draft object on success, or an error dictionary on failure

    Notes:
    ------
    - The draft is saved to the user's Drafts folder.
    - Recipient lists accept simple email strings; function builds correct schema.
    """
    client = get_outlookMail_client()
    if not client:
        logger.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/messages"
    payload = {
        "subject": subject,
        "body": {
            "contentType": "HTML",
            "content": body_content
        }
    }


    # Recipient fields to add dynamically
    recipient_fields = {
        "toRecipients": to_recipients,
        "ccRecipients": cc_recipients,
        "bccRecipients": bcc_recipients
    }

    for key, emails in recipient_fields.items():
        if emails:
            payload[key] = [{"emailAddress": {"address": email}} for email in emails]

    try:
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.post(url, headers=client['headers'], json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Could not create Outlook draft message at {url}: {e}")
        return {"error": f"Could not create Outlook draft message at {url}"}

async def outlookMail_update_draft(
    message_id: str,
    subject: str = None,
    body_content: str = None,
    to_recipients: list = None,
    cc_recipients: list = None,
    bcc_recipients: list = None,
) -> dict:
    """
    Updates an existing Outlook draft message using Microsoft Graph API (PATCH method)

    Required parameter:
    message_id (str): ID of the draft message to update (e.g., "AAMkAGM2...")

    Draft-Specific Parameters (updatable only in draft state):
    subject (str): Message subject
    body_content (str): HTML content of the message body
    internet_message_id (str): RFC2822 message ID
    reply_to (list): Email addresses for reply-to
    toRecipients/ccRecipients/bccRecipients (list): Recipient email addresses

    Returns:
    dict: Updated message object on success, error dictionary on failure

    Parameter Structures:
    --------------------
    1. Recipient Structure (for from_sender/sender):
        {
            "emailAddress": {
                "address": "user@domain.com",    # REQUIRED email
                "name": "Display Name"           # Optional display name
            }
        }

    2. followupFlag Structure (for flag parameter):
        {
            "completedDateTime": {   # Completion date/time
                "dateTime": "yyyy-MM-ddThh:mm:ss",
                "timeZone": "TimezoneName"
            },
            "dueDateTime": {         # Due date/time (requires startDateTime)
                "dateTime": "yyyy-MM-ddThh:mm:ss",
                "timeZone": "TimezoneName"
            },
            "flagStatus": "flagged", # "notFlagged", "flagged", "complete"
            "startDateTime": {       # Start date/time
                "dateTime": "yyyy-MM-ddThh:mm:ss",
                "timeZone": "TimezoneName"
            }
        }

    3. Body Structure (handled automatically from body_content):
        {
            "contentType": "HTML",   # Fixed as HTML
            "content": "<html>...</html>"
        }
    """
    client = get_outlookMail_client()
    if not client:
        logger.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/messages/{message_id}"
    payload = {}

    # Add plain fields
    fields = {
        "subject": subject,
    }

    for key, value in fields.items():
        if value is not None:
            payload[key] = value

    # Add body if provided
    if body_content:
        payload["body"] = {
            "contentType": "HTML",
            "content": body_content
        }

    # Add recipients
    recipient_fields = {
        "toRecipients": to_recipients,
        "ccRecipients": cc_recipients,
        "bccRecipients": bcc_recipients
    }

    for key, emails in recipient_fields.items():
        if emails:
            payload[key] = [{"emailAddress": {"address": email}} for email in emails]

    try:
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.patch(url, headers=client['headers'], json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Could not update Outlook draft message at {url}: {e}")
        return {"error": f"Could not update Outlook draft message at {url}"}


async def outlookMail_delete_draft(message_id: str) -> dict:
    """
    Delete an existing Outlook draft message by message ID.

    Args:
        message_id (str): The ID of the draft message to Delete.

    Returns:
        dict: JSON response from Microsoft Graph API with updated draft details,
              or an error message if the request fails.
    """
    client = get_outlookMail_client()
    if not client:
        logger.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/messages/{message_id}"

    try:
        logger.info(f"Deleting draft Outlook mail message at {url}")
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.delete(url, headers=client['headers'])
        if response.status_code == 204:
            return {"Success":"Deleted"}
        else:
            logger.warning(f"Unexpected status code: {response.status_code}")
            # try to parse error if there is one
            try:
                error_response = response.json()
                logger.error(f"Delete failed with response: {error_response}")
                return error_response
            except Exception as parse_error:
                logger.error(f"Could not parse error response: {parse_error}")
                return {"error": f"Unexpected response: {response.status_code}"}
    except Exception as e:
        logger.error(f"Could not delete Outlook draft message at {url}: {e}")
        return {"error": f"Could not delete Outlook draft message at {url}"}


async def outlookMail_create_forward_draft(
        message_id: str,
        comment: str,
        to_recipients: list
) -> dict:
    """
    Create a draft forward message for an existing Outlook message.

    Args:
        message_id (str): ID of the original message to forward.
        comment (str): Comment to include in the forwarded message.
        to_recipients (list): List of recipient email addresses as strings.

    Returns:
        dict: JSON response from Microsoft Graph API with the created draft forward's details,
              or an error message if the request fails.
    """
    client = get_outlookMail_client()  # same method you used to get your client and headers
    if not client:
        logger.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/messages/{message_id}/createForward"

    # Build recipient list in required format
    recipients = [{"emailAddress": {"address": email}} for email in to_recipients]

    payload = {
        "comment": comment,
        "toRecipients": recipients
    }

    try:
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.post(url, headers=client['headers'], json=payload)
            return response.json()
    except Exception as e:
        logger.error(f"Could not create Outlook forward draft message at {url}: {e}")
        return {"error": f"Could not create Outlook forward draft message at {url}"}

async def outlookMail_create_reply_draft(
        message_id: str,
        comment: str
) -> dict:
    """
    Create a draft reply message to an existing Outlook message.

    Args:
        message_id (str): ID of the original message to reply to.
        comment (str): Comment to include in the reply.


    Returns:
        dict: JSON response from Microsoft Graph API with the created draft reply's details,
              or an error message if the request fails.
    """
    client = get_outlookMail_client()
    if not client:
        logger.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/messages/{message_id}/createReply"

    payload = {
        "comment": comment
    }


    try:
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.post(url, headers=client['headers'], json=payload)
            return response.json()
    except Exception as e:
        logger.error(f"Could not create Outlook reply draft message at {url}: {e}")
        return {"error": f"Could not create Outlook reply draft message at {url}"}


async def outlookMail_create_reply_all_draft(
        message_id: str,
        comment: str = ""
) -> dict:
    """
    Create a reply-all draft to an existing Outlook message.

    Args:
        message_id (str): The ID of the message you want to reply to.
        comment (str, optional): Text to include in the reply body.

    Returns:
        dict: JSON response from Microsoft Graph API with the draft details,
              or an error message if the request fails.
    """
    client = get_outlookMail_client()  # reuse your existing token logic
    if not client:
        logger.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/messages/{message_id}/createReplyAll"

    payload = {
        "comment": comment
    }

    try:
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.post(url, headers=client['headers'], json=payload)
            return response.json()
    except Exception as e:
        logger.error(f"Could not create reply-all draft at {url}: {e}")
        return {"error": f"Could not create reply-all draft at {url}"}

async def outlookMail_send_draft(message_id: str) -> dict:
    """
    Send an existing draft Outlook mail message by message ID.

    Args:
        message_id (str): The ID of the draft message to send.

    Returns:
        dict: Empty response if successful, or error details.
    """
    client = get_outlookMail_client()
    if not client:
        logger.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/messages/{message_id}/send"

    try:
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.post(url, headers=client['headers'])
        if response.status_code == 202 or response.status_code == 200 or response.status_code == 204:
            logger.info("Draft sent successfully")
            return {"success": "Draft sent successfully"}
        else:
            try:
                return response.json()
            except Exception:
                return {"error": f"Unexpected response: {response.status_code}"}
    except Exception as e:
        logger.error(f"Could not send Outlook draft message at {url}: {e}")
        return {"error": f"Could not send Outlook draft message at {url}"}

async def outlookMail_move_message(
        message_id: str,
        destination_folder_id: str
) -> dict:
    """
    Move an Outlook mail message to another folder.

    Args:
        message_id (str): ID of the message to move.
        destination_folder_id (str): ID of the target folder.
                                     Example: 'deleteditems' or actual folder ID.

    Returns:
        dict: JSON response from Microsoft Graph API with moved message details,
              or an error message if it fails.
    """
    client = get_outlookMail_client()
    if not client:
        logger.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/messages/{message_id}/move"

    payload = {
        "destinationId": destination_folder_id
    }

    try:
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.post(url, headers=client['headers'], json=payload)
            return response.json()
    except Exception as e:
        logger.error(f"Could not move Outlook mail message at {url}: {e}")
        return {"error": f"Could not move Outlook mail message at {url}"}


if __name__ == "__main__":
    #print(await outlookMail_create_draft('dss','sds','dsds'))
    pass