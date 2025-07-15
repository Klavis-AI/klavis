import requests
import logging
from .base import get_onedrive_client

# Configure logging
logger = logging.getLogger(__name__)

async def outlookMail_list_inbox_rules() -> dict:
    """
    List all message rules (inbox rules) from the user's Inbox folder.

    Returns:
        dict: JSON response from Microsoft Graph API with the list of rules,
              or an error message if the request fails.
    """
    client = get_onedrive_client()  # same method you already use to get auth + base_url
    if not client:
        logger.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders/inbox/messageRules"

    try:
        response = requests.get(url, headers=client['headers'])
        response.raise_for_status()
        logger.info("Retrieved inbox message rules")
        return response.json()
    except Exception as e:
        logger.error(f"Could not get inbox message rules from {url}: {e}")
        return {"error": f"Could not get inbox message rules from {url}: {e}"}


async def outlookMail_get_inbox_rule_by_id(rule_id: str) -> dict:
    """
    Get a specific inbox message rule by its ID.

    Args:
        rule_id (str): The unique ID of the inbox rule to retrieve.

    Returns:
        dict: JSON response from Microsoft Graph API with rule details,
              or an error message if the request fails.
    """
    client = get_onedrive_client()
    if not client:
        logger.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders/inbox/messageRules/{rule_id}"

    try:
        response = requests.get(url, headers=client['headers'])
        response.raise_for_status()
        logger.info(f"Fetched inbox message rule {rule_id}")
        return response.json()
    except Exception as e:
        logger.error(f"Could not get inbox rule {rule_id} at {url}: {e}")
        return {"error": f"Could not get inbox rule {rule_id} at {url}: {e}"}


async def outlookMail_create_message_rule(
        displayName : str,
        sequence : int,
        actions : dict,
        isEnabled : bool = True,
        conditions : dict = None,
        exceptions : dict = None,
        ) -> dict:
    """
        Creates a new Outlook message rule using Microsoft Graph API

        Required parameters:
        displayName (str): Rule display name
        sequence (int): Execution order among other rules (lower values execute first)
        actions (dict): Actions to apply when conditions are met (see structure below)

        Optional parameters:
        isEnabled (bool): Whether the rule is active (default: True)
        conditions (dict): Conditions triggering the rule (empty = all messages)
        exceptions (dict): Exception conditions preventing rule execution

        Returns:
        dict: Created rule object on success, error dictionary on failure

        Parameter Structures:
        --------------------
        1. actions (messageRuleActions - REQUIRED):
            {
                "assignCategories": [str],           # Categories to apply
                "copyToFolder": str,                 # Folder ID for copying
                "delete": bool,                      # Move to Deleted Items
                "forwardAsAttachmentTo": [recipient],# Forward as attachment
                "forwardTo": [recipient],            # Standard forward
                "markAsRead": bool,                  # Mark as read
                "markImportance": str,               # "low", "normal", "high"
                "moveToFolder": str,                 # Folder ID for moving
                "permanentDelete": bool,             # Skip Deleted Items
                "redirectTo": [recipient],           # Redirect recipients
                "stopProcessingRules": bool          # Halt further rules
            }

        2. conditions/exceptions (messageRulePredicates - OPTIONAL):
            {
                "bodyContains": [str],               # Body substring matches
                "bodyOrSubjectContains": [str],      # Body/subject matches
                "categories": [str],                 # Assigned categories
                "fromAddresses": [recipient],        # Specific senders
                "hasAttachments": bool,              # Attachment presence
                "headerContains": [str],             # Header substring matches
                "importance": str,                   # "low", "normal", "high"
                "isApprovalRequest": bool,           # Approval requests
                "isAutomaticForward": bool,          # Auto-forwarded messages
                "isAutomaticReply": bool,            # Auto-replies
                "isEncrypted": bool,                 # Encrypted messages
                "isMeetingRequest": bool,            # Meeting requests
                "isMeetingResponse": bool,           # Meeting responses
                "isNonDeliveryReport": bool,         # NDR messages
                "isPermissionControlled": bool,      # RMS-protected messages
                "isReadReceipt": bool,              # Read receipts
                "isSigned": bool,                   # S/MIME signed
                "isVoicemail": bool,                # Voice messages
                "messageActionFlag": str,            # "any", "call", "forward", etc.
                "notSentToMe": bool,                # Excludes mailbox owner
                "recipientContains": [str],          # To/Cc recipient strings
                "senderContains": [str],             # From address strings
                "sensitivity": str,                 # "normal", "personal", "private"
                "sentCcMe": bool,                   # Owner in Cc
                "sentOnlyToMe": bool,               # Owner is sole recipient
                "sentToAddresses": [recipient],      # Specific recipients
                "sentToMe": bool,                   # Owner in To
                "sentToOrCcMe": bool,               # Owner in To/Cc
                "subjectContains": [str],            # Subject substrings
                "withinSizeRange": {                # Size in kilobytes
                    "minimumSize": int,
                    "maximumSize": int
                }
            }

        3. recipient Structure (used in actions/conditions):
            {
                "emailAddress": {
                    "address": "user@domain.com",    # Email address (REQUIRED)
                    "name": "Display Name"           # Optional display name
                }
            }

        Example Usage:
        --------------
        Create rule to move high-importance emails from manager to folder:

        conditions = {
            "fromAddresses": [{
                "emailAddress": {
                    "address": "manager@contoso.com"
                }
            }],
            "importance": "high"
        }

        actions = {
            "moveToFolder": "AAMkAGM2...",
            "markAsRead": True
        }

        response = outlookMail_create_message_rule(
            displayName="Move Manager Urgent",
            sequence=1,
            actions=actions,
            conditions=conditions
        )
    """

    client = get_onedrive_client()
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders/inbox/messageRules"

    payload = {}

    args = {
        "displayName": displayName,
        "sequence": sequence,
        "isEnabled": isEnabled,
        "conditions": conditions,
        "actions": actions,
        "exceptions": exceptions,
    }

    for key, value in args.items():
        if value is not None:
            payload[key] = value

    try:
        response = requests.post(url, headers=client['headers'], json=payload)
        response.raise_for_status()
        logging.info("Created Outlook message rule")
        return response.json()
    except Exception as e:
        logging.error(f"Could not create Outlook message rule at {url}: {e}")
        return {"error": f"Could not create Outlook message rule at {url}"}


async def outlookMail_update_message_rule(
    rule_id: str,
    displayName: str = None,
    sequence: int = None,
    isEnabled: bool = None,
    actions: dict = None,
    conditions: dict = None,
    exceptions: dict = None
) -> dict:
    """
        Updates an existing Outlook message rule using Microsoft Graph API (PATCH method)

        Required parameter:
        rule_id (str): The ID of the message rule to update.
                       Format: Microsoft Graph messageRule ID (e.g., "AQAAA...")

        Updateable parameters (at least one required):
        displayName (str): New display name for the rule
        sequence (int): New execution order (lower values execute first)
        isEnabled (bool): Enable/disable status of the rule
        actions (dict): New actions to apply when conditions are met
        conditions (dict): New triggering conditions (set empty dict to match all messages)
        exceptions (dict): New exception conditions

        Returns:
        dict: Updated rule object on success, error dictionary on failure

        Parameter Structures:
        --------------------
        1. actions (messageRuleActions - OPTIONAL update):
            {
                "assignCategories": [str],           # Categories to apply
                "copyToFolder": str,                 # Folder ID for copying
                "delete": bool,                      # Move to Deleted Items
                "forwardAsAttachmentTo": [recipient],# Forward as attachment
                "forwardTo": [recipient],            # Standard forward
                "markAsRead": bool,                  # Mark as read
                "markImportance": str,               # "low", "normal", "high"
                "moveToFolder": str,                 # Folder ID for moving
                "permanentDelete": bool,             # Skip Deleted Items
                "redirectTo": [recipient],           # Redirect recipients
                "stopProcessingRules": bool          # Halt further rules
            }

        2. conditions/exceptions (messageRulePredicates - OPTIONAL update):
            {
                "bodyContains": [str],               # Body substring matches
                "bodyOrSubjectContains": [str],      # Body/subject matches
                "categories": [str],                 # Assigned categories
                "fromAddresses": [recipient],        # Specific senders
                "hasAttachments": bool,              # Attachment presence
                "headerContains": [str],             # Header substring matches
                "importance": str,                   # "low", "normal", "high"
                "isApprovalRequest": bool,           # Approval requests
                "isAutomaticForward": bool,          # Auto-forwarded messages
                "isAutomaticReply": bool,            # Auto-replies
                "isEncrypted": bool,                 # Encrypted messages
                "isMeetingRequest": bool,            # Meeting requests
                "isMeetingResponse": bool,           # Meeting responses
                "isNonDeliveryReport": bool,         # NDR messages
                "isPermissionControlled": bool,      # RMS-protected messages
                "isReadReceipt": bool,              # Read receipts
                "isSigned": bool,                   # S/MIME signed
                "isVoicemail": bool,                # Voice messages
                "messageActionFlag": str,            # "any", "call", "forward", etc.
                "notSentToMe": bool,                # Excludes mailbox owner
                "recipientContains": [str],          # To/Cc recipient strings
                "senderContains": [str],             # From address strings
                "sensitivity": str,                 # "normal", "personal", "private"
                "sentCcMe": bool,                   # Owner in Cc
                "sentOnlyToMe": bool,               # Owner is sole recipient
                "sentToAddresses": [recipient],      # Specific recipients
                "sentToMe": bool,                   # Owner in To
                "sentToOrCcMe": bool,               # Owner in To/Cc
                "subjectContains": [str],            # Subject substrings
                "withinSizeRange": {                # Size in kilobytes
                    "minimumSize": int,
                    "maximumSize": int
                }
            }

        3. recipient Structure (used in actions/conditions):
            {
                "emailAddress": {
                    "address": "user@domain.com",    # Email address (REQUIRED)
                    "name": "Display Name"           # Optional display name
                }
            }

        Key Notes:
        ----------
        1. PATCH semantics: Only provided fields will be updated
        2. Rule scope: Updates rules in the user's inbox folder only
        3. Null handling: Passing None maintains existing value
        4. Clearing values:
           - Use empty list [] to clear array fields
           - Use False/empty string for scalar fields
           - Conditions: Set to empty dict {} to match all messages
        5. Validation: Server enforces schema requirements on updated fields

        Example Usage:
        --------------
        # Partial update: Disable rule and change priority
        response = outlookMail_update_message_rule(
            rule_id="AQAAA5fTHs0=",
            isEnabled=False,
            sequence=5
        )

        # Full actions/conditions update:
        conditions = {
            "subjectContains": ["URGENT"],
            "fromAddresses": [{
                "emailAddress": {"address": "alerts@contoso.com"}
            }]
        }

        actions = {
            "forwardTo": [{
                "emailAddress": {"address": "team@contoso.com"}
            }],
            "stopProcessingRules": True
        }

        response = outlookMail_update_message_rule(
            rule_id="AQAAA5fTHs0=",
            displayName="Urgent Forward Rule",
            sequence=1,
            conditions=conditions,
            actions=actions
        )

        # Clear conditions (match all messages):
        outlookMail_update_message_rule(
            rule_id="AQAAA5fTHs0=",
            conditions={}
        )
    """
    client = get_onedrive_client()
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders/inbox/messageRules/{rule_id}"

    payload = {}

    args = {
        "displayName": displayName,
        "sequence": sequence,
        "isEnabled": isEnabled,
        "actions": actions,
        "conditions": conditions,
        "exceptions": exceptions
    }

    for key, value in args.items():
        if value is not None:
            payload[key] = value

    try:
        response = requests.patch(url, headers=client['headers'], json=payload)
        response.raise_for_status()
        logging.info("Updated Outlook message rule")
        return response.json()
    except Exception as e:
        logging.error(f"Could not update Outlook message rule at {url}: {e}")
        return {"error": f"Could not update Outlook message rule at {url}"}

async def outlookMail_delete_message_rule(rule_id: str) -> dict:
    """
    Delete an Outlook message rule from the inbox using Microsoft Graph API.

    Args:
        rule_id (str): ID of the message rule to delete.

    Returns:
        dict: {"status": "Deleted"} on success, or {"error": "..."} on failure.
    """

    client = get_onedrive_client()
    if not client:
        logging.error("Could not get Outlook client")
        return {"error": "Could not get Outlook client"}

    url = f"{client['base_url']}/me/mailFolders/inbox/messageRules/{rule_id}"

    try:
        response = requests.delete(url, headers=client['headers'])
        response.raise_for_status()
        logging.info(f"Deleted Outlook message rule: {rule_id}")
        return {"status": "Deleted"}
    except Exception as e:
        logging.error(f"Could not delete Outlook message rule at {url}: {e}")
        return {"error": f"Could not delete Outlook message rule at {url}"}
