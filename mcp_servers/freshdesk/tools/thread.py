import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from .base import make_freshdesk_request, handle_freshdesk_error, remove_none_values, handle_freshdesk_attachments

# Configure logging
logger = logging.getLogger(__name__)


async def create_thread(
    thread_type: str,
    parent_id: int,
    parent_type: str = "ticket",
    title: Optional[str] = None,
    created_by: Optional[str] = None,
    anchor_id: Optional[int] = None,
    anchor_type: Optional[str] = None,
    participants_emails: Optional[List[str]] = None,
    participants_agents: Optional[List[str]] = None,
    additional_info: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a new thread in Freshdesk.
    
    Args:
        thread_type: Type of thread (forward, discussion, private)
        parent_id: ID of the parent object (usually ticket)
        parent_type: Type of parent object (default: ticket)
        title: Title of the thread
        created_by: ID of the user creating the thread
        anchor_id: ID of the anchor object (e.g., conversation ID)
        anchor_type: Type of anchor object (e.g., conversation)
        participants_emails: List of email addresses of participants
        participants_agents: List of agent IDs of participants
        additional_info: Additional information like email_config_id
        **kwargs: Additional thread fields
        
    Returns:
        Dictionary containing the created thread details
    """
    try:
        thread_data = {
            "type": thread_type,
            "parent": {
                "id": str(parent_id),
                "type": parent_type
            },
            "title": title,
            "created_by": created_by,
            "additional_info": additional_info,
            **kwargs
        }

        # Add anchor if provided
        if anchor_id and anchor_type:
            thread_data["anchor"] = {
                "id": str(anchor_id),
                "type": anchor_type
            }

        # Add participants if provided
        if participants_emails or participants_agents:
            thread_data["participants"] = {}
            if participants_emails:
                thread_data["participants"]["emails"] = participants_emails
            if participants_agents:
                thread_data["participants"]["agents"] = participants_agents

        thread_data = remove_none_values(thread_data)
        
        logger.info(f"Creating thread with data: {thread_data}")
        
        response = await make_freshdesk_request(
            method="POST",
            endpoint="/collaboration/threads",
            data=thread_data
        )
        
        logger.info(f"Successfully created thread")
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "create", "thread")


async def get_thread_by_id(thread_id: int) -> Dict[str, Any]:
    """
    Get a thread by its ID.
    
    Args:
        thread_id: ID of the thread to retrieve
        
    Returns:
        Dictionary containing the thread details
    """
    try:
        logger.info(f"Retrieving thread with ID: {thread_id}")
        
        response = await make_freshdesk_request(
            method="GET",
            endpoint=f"/collaboration/threads/{thread_id}"
        )
        
        logger.info(f"Successfully retrieved thread")
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "get", "thread")


async def update_thread(
    thread_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Update a thread in Freshdesk.
    
    Args:
        thread_id: ID of the thread to update
        title: New title for the thread
        description: New description for the thread
        **kwargs: Additional fields to update
        
    Returns:
        Dictionary containing the updated thread details
    """
    try:
        thread_data = {
            "title": title,
            "description": description,
            **kwargs
        }
        
        thread_data = remove_none_values(thread_data)
        
        logger.info(f"Updating thread {thread_id} with data: {thread_data}")
        
        response = await make_freshdesk_request(
            method="PUT",
            endpoint=f"/collaboration/threads/{thread_id}",
            data=thread_data
        )
        
        logger.info(f"Successfully updated thread")
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "update", "thread")


async def delete_thread(thread_id: int) -> Dict[str, Any]:
    """
    Delete a thread from Freshdesk.
    Note: This is an irreversible action!
    
    Args:
        thread_id: ID of the thread to delete
        
    Returns:
        Dictionary containing the deletion result
    """
    try:
        logger.info(f"Deleting thread with ID: {thread_id}")
        
        response = await make_freshdesk_request(
            method="DELETE",
            endpoint=f"/collaboration/threads/{thread_id}"
        )
        
        logger.info(f"Successfully deleted thread")
        return {"success": True, "message": f"Thread {thread_id} deleted successfully"}
        
    except Exception as e:
        return handle_freshdesk_error(e, "delete", "thread")


async def create_thread_message(
    thread_id: int,
    body: str,
    body_text: Optional[str] = None,
    attachment_ids: Optional[List[int]] = None,
    inline_attachment_ids: Optional[List[int]] = None,
    participants_email_to: Optional[List[str]] = None,
    participants_email_cc: Optional[List[str]] = None,
    participants_email_bcc: Optional[List[str]] = None,
    participants_email_from: Optional[str] = None,
    additional_info: Optional[Dict[str, Any]] = None,
    full_message: Optional[str] = None,
    full_message_text: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a new message for a thread.
    
    Args:
        thread_id: ID of the thread to add message to
        body: HTML content of the message
        body_text: Plain text content of the message
        attachment_ids: List of attachment IDs to include
        inline_attachment_ids: List of inline attachment IDs
        participants_email_to: List of email addresses to send to
        participants_email_cc: List of email addresses to CC
        participants_email_bcc: List of email addresses to BCC
        participants_email_from: Email address to send from
        additional_info: Additional information like has_quoted_text, email_subject
        full_message: HTML content with original and quoted text
        full_message_text: Plain text with quoted text
        **kwargs: Additional message fields
        
    Returns:
        Dictionary containing the created message details
    """
    try:
        message_data = {
            "thread_id": str(thread_id),
            "body": body,
            "body_text": body_text,
            "attachment_ids": attachment_ids,
            "inline_attachment_ids": inline_attachment_ids,
            "full_message": full_message,
            "full_message_text": full_message_text,
            "additional_info": additional_info,
            **kwargs
        }

        # Add participants if provided
        if any([participants_email_to, participants_email_cc, participants_email_bcc, participants_email_from]):
            message_data["participants"] = {
                "email": {}
            }
            
            if participants_email_to:
                message_data["participants"]["email"]["to"] = participants_email_to
            if participants_email_cc:
                message_data["participants"]["email"]["cc"] = participants_email_cc
            if participants_email_bcc:
                message_data["participants"]["email"]["bcc"] = participants_email_bcc
            if participants_email_from:
                message_data["participants"]["email"]["from"] = participants_email_from

        message_data = remove_none_values(message_data)
        
        logger.info(f"Creating message for thread {thread_id} with data: {message_data}")
        
        response = await make_freshdesk_request(
            method="POST",
            endpoint="/collaboration/messages",
            data=message_data
        )
        
        logger.info(f"Successfully created thread message")
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "create", "thread message")


async def get_thread_message_by_id(message_id: int) -> Dict[str, Any]:
    """
    Get a thread message by its ID.
    
    Args:
        message_id: ID of the message to retrieve
        
    Returns:
        Dictionary containing the message details
    """
    try:
        logger.info(f"Retrieving thread message with ID: {message_id}")
        
        response = await make_freshdesk_request(
            method="GET",
            endpoint=f"/collaboration/messages/{message_id}"
        )
        
        logger.info(f"Successfully retrieved thread message")
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "get", "thread message")


async def update_thread_message(
    message_id: int,
    body: Optional[str] = None,
    body_text: Optional[str] = None,
    attachment_ids: Optional[List[int]] = None,
    inline_attachment_ids: Optional[List[int]] = None,
    additional_info: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Update a thread message.
    
    Args:
        message_id: ID of the message to update
        body: New HTML content of the message
        body_text: New plain text content of the message
        attachment_ids: New list of attachment IDs
        inline_attachment_ids: New list of inline attachment IDs
        additional_info: New additional information
        **kwargs: Additional fields to update
        
    Returns:
        Dictionary containing the updated message details
    """
    try:
        message_data = {
            "body": body,
            "body_text": body_text,
            "attachment_ids": attachment_ids,
            "inline_attachment_ids": inline_attachment_ids,
            "additional_info": additional_info,
            **kwargs
        }
        
        message_data = remove_none_values(message_data)
        
        logger.info(f"Updating thread message {message_id} with data: {message_data}")
        
        response = await make_freshdesk_request(
            method="PUT",
            endpoint=f"/collaboration/messages/{message_id}",
            data=message_data
        )
        
        logger.info(f"Successfully updated thread message")
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "update", "thread message")


async def delete_thread_message(message_id: int) -> Dict[str, Any]:
    """
    Delete a thread message.
    Note: This is an irreversible action!
    
    Args:
        message_id: ID of the message to delete
        
    Returns:
        Dictionary containing the deletion result
    """
    try:
        logger.info(f"Deleting thread message with ID: {message_id}")
        
        response = await make_freshdesk_request(
            method="DELETE",
            endpoint=f"/collaboration/messages/{message_id}"
        )
        
        logger.info(f"Successfully deleted thread message")
        return {"success": True, "message": f"Thread message {message_id} deleted successfully"}
        
    except Exception as e:
        return handle_freshdesk_error(e, "delete", "thread message")
