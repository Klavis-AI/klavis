import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from .base import make_freshdesk_request, handle_freshdesk_error

# Configure logging
logger = logging.getLogger(__name__)

# Ticket statuses
STATUS_OPEN = 2
STATUS_PENDING = 3
STATUS_RESOLVED = 4
STATUS_CLOSED = 5

# Ticket priorities
PRIORITY_LOW = 1
PRIORITY_MEDIUM = 2
PRIORITY_HIGH = 3
PRIORITY_URGENT = 4

# Ticket sources
SOURCE_EMAIL = 1
SOURCE_PORTAL = 2
SOURCE_PHONE = 3
SOURCE_CHAT = 7
SOURCE_FEEDBACK = 9
SOURCE_OUTBOUND_EMAIL = 10




def create_ticket(
    subject: str,
    description: str,
    email: str,
    name: Optional[str] = None,
    priority: int = PRIORITY_MEDIUM,
    status: int = STATUS_OPEN,
    source: int = SOURCE_PORTAL,
    tags: Optional[List[str]] = None,
    custom_fields: Optional[Dict[str, Any]] = None,
    cc_emails: Optional[List[str]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a new ticket in Freshdesk.
    
    Args:
        subject: Subject of the ticket
        description: HTML content of the ticket
        email: Email address of the requester
        name: Name of the requester (required if email not provided)
        priority: Priority of the ticket (1-4)
        status: Status of the ticket (2-5)
        source: Source of the ticket (1-10)
        tags: List of tags to associate with the ticket
        custom_fields: Key-value pairs of custom fields
        cc_emails: List of email addresses to CC
        **kwargs: Additional ticket fields (e.g., due_by, fr_due_by, group_id, etc.)
        
    Returns:
        Dictionary containing the created ticket details
    """
    try:
        attachments = kwargs.pop("attachments", None)

        ticket_data = {
            "subject": subject,
            "description": description,
            "email": email,
            "priority": priority,
            "status": status,
            "source": source,
            **kwargs
        }

        options = { }
        
        if name:
            ticket_data["name"] = name
            
        if tags:
            ticket_data["tags"] = tags
            
        if custom_fields:
            ticket_data["custom_fields"] = custom_fields
            
        if cc_emails:
            ticket_data["cc_emails"] = cc_emails
            
        # Handle attachments if provided
        if attachments:
            options["files"] = attachments
            options["headers"] = {
                "Content-Type": "multipart/form-data",
            }
        
        logger.info(f"Creating ticket with data: {ticket_data}")
        response = make_freshdesk_request("POST", "/tickets", data=ticket_data, options=options)
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "create", "ticket")



def create_ticket_with_attachments(
    subject: str,
    description: str,
    email: str,
    name: Optional[str] = None,
    priority: int = PRIORITY_MEDIUM,
    status: int = STATUS_OPEN,
    source: int = SOURCE_PORTAL,
    tags: Optional[List[str]] = None,
    custom_fields: Optional[Dict[str, Any]] = None,
    cc_emails: Optional[List[str]] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
    **kwargs
): 
    try:
       return freshdesk_create_ticket(
           subject=subject,
           description=description,
           email=email,
           name=name,
           priority=priority,
           status=status,
           source=source,
           tags=tags,
           custom_fields=custom_fields,
           cc_emails=cc_emails,
           attachments=attachments,
           **kwargs
       )
    except Exception as e:
        return handle_freshdesk_error(e, "create", "ticket")


def get_ticket(ticket_id: int, include_conversations: bool = False) -> Dict[str, Any]:
    """
    Retrieve a ticket by its ID.
    
    Args:
        ticket_id: ID of the ticket to retrieve
        include_conversations: Whether to include conversation history
        
    Returns:
        Dictionary containing ticket details
    """
    try:
        endpoint = f"/tickets/{ticket_id}"
        if include_conversations:
            endpoint += "?include=conversations"
            
        response = make_freshdesk_request("GET", endpoint)
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "retrieve", "ticket")


def update_ticket(
    ticket_id: int,
    subject: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[int] = None,
    status: Optional[int] = None,
    tags: Optional[List[str]] = None,
    custom_fields: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Update an existing ticket.
    
    Args:
        ticket_id: ID of the ticket to update
        subject: New subject (if updating)
        description: New description (if updating)
        priority: New priority (1-4, if updating)
        status: New status (2-5, if updating)
        tags: New tags (if updating)
        custom_fields: Updated custom fields (if any)
        **kwargs: Additional fields to update
        
    Returns:
        Dictionary containing updated ticket details
    """
    try:
        update_data = {}
        
        if subject is not None:
            update_data["subject"] = subject
        if description is not None:
            update_data["description"] = description
        if priority is not None:
            update_data["priority"] = priority
        if status is not None:
            update_data["status"] = status
        if tags is not None:
            update_data["tags"] = tags
        if custom_fields is not None:
            update_data["custom_fields"] = custom_fields
            
        update_data.update(kwargs)
        
        if not update_data:
            return {"success": False, "error": "No fields to update"}
            
        logger.info(f"Updating ticket {ticket_id} with data: {update_data}")
        response = make_freshdesk_request("PUT", f"/tickets/{ticket_id}", data=update_data)
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "update", "ticket")


def delete_ticket(ticket_id: int) -> Dict[str, Any]:
    """
    Delete a ticket.
    
    Args:
        ticket_id: ID of the ticket to delete
        
    Returns:
        Dictionary indicating success or failure
    """
    try:
        endpoint = f"/tickets/{ticket_id}"
            
        make_freshdesk_request("DELETE", endpoint)
        return {"success": True, "message": f"Ticket {ticket_id} deleted successfully"}
        
    except Exception as e:
        return handle_freshdesk_error(e, "delete", "ticket")



def delete_multiple_tickets(ticket_ids: List[int]) -> Dict[str, Any]: 
    """
    Delete multiple tickets.
    
    Args:
        ticket_ids: List of IDs of tickets to delete
        
    Returns:
        Dictionary indicating success or failure
    """

    try:

        if not ticket_ids:
            return {"success": False, "error": "No ticket IDs provided"}

        endpoint = "/tickets/bulk_delete"
        data = {"bulk_action":{
            "ids": ticket_ids
        }}
        make_freshdesk_request("POST", endpoint, data=data)
        return {"success": True, "message": f"Tickets {ticket_ids} deleted successfully"}
    except Exception as e:
        return handle_freshdesk_error(e, "delete", "tickets")


def delete_attachment(attachment_id: int) -> Dict[str, Any]:
    """
    Delete an attachment from a ticket.
    
    Args:
        attachment_id: ID of the attachment to delete
        
    Returns:
        Dictionary indicating success or failure
    """
    try:
        endpoint = f"/attachments/{attachment_id}"
            
        make_freshdesk_request("DELETE", endpoint)
        return {"success": True, "message": f"Attachment {attachment_id} deleted successfully"}
        
    except Exception as e:
        return handle_freshdesk_error(e, "delete", "attachment")
    

def list_tickets(
    status: Optional[int] = None,
    priority: Optional[int] = None,
    requester_id: Optional[int] = None,
    group_id: Optional[int] = None,
    updated_since: Optional[Union[str, datetime]] = None,
    page: int = 1,
    per_page: int = 30,
    **filters
) -> Dict[str, Any]:
    """
    List tickets with optional filtering.
    
    Args:
        status: Filter by status (2-5)
        priority: Filter by priority (1-4)
        requester_id: Filter by requester ID
        group_id: Filter by group ID
        updated_since: Only return tickets updated since this date (ISO format or datetime object)
        page: Page number (for pagination)
        per_page: Number of results per page (max 100)
        **filters: Additional filters as keyword arguments
        
    Returns:
        Dictionary containing list of tickets and pagination info
    """
    try:
        params = {
            "page": page,
            "per_page": min(per_page, 100) 
        }
        
        if status is not None:
            params["status"] = status
        if priority is not None:
            params["priority"] = priority
        if requester_id is not None:
            params["requester_id"] = requester_id
        if group_id is not None:
            params["group_id"] = group_id
        if updated_since is not None:
            if isinstance(updated_since, datetime):
                updated_since = updated_since.isoformat()
            params["updated_since"] = updated_since
            
        params.update(filters)
        
        response = make_freshdesk_request(
            "GET", 
            "/tickets", 
            options={"query_params": params}
        )
        
        if isinstance(response, list):
            return {
                "tickets": response,
                "page": page,
                "per_page": per_page,
                "total": len(response)
            }
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "list", "tickets")


def add_note_to_ticket(
    ticket_id: int,
    body: str,
    private: bool = False,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Add a note to a ticket.
    
    Args:
        ticket_id: ID of the ticket
        body: Content of the note
        private: Whether the note is private
        user_id: ID of the agent adding the note (defaults to authenticated user)
        
    Returns:
        Dictionary containing the created note details
    """
    try:
        note_data = {
            "body": body,
            "private": private
        }
        
        if user_id is not None:
            note_data["user_id"] = user_id
            
        response = make_freshdesk_request(
            "POST",
            f"/tickets/{ticket_id}/notes",
            data=note_data
        )
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "add note to", "ticket")


def search_tickets(
    query: str,
    page: int = 1,
    per_page: int = 30
) -> Dict[str, Any]:
    """
    Search for tickets using Freshdesk's search syntax.
    
    Args:
        query: Search query string (e.g., "priority:3 AND status:2")
        page: Page number (for pagination)
        per_page: Number of results per page (max 30)
        
    Returns:
        Dictionary containing search results and pagination info
    """
    try:
        params = {
            "query": f'"{query}"',
            "page": page,
            "per_page": min(per_page, 30)
        }
        
        response = make_freshdesk_request(
            "GET",
            "/search/tickets",
            options={"query_params": params}
        )
        
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "search", "tickets")



def merge_tickets(source_ticket_id: int, target_ticket_id: int) -> Dict[str, Any]:
    """
    Merge two tickets.
    
    Args:
        source_ticket_id: ID of the ticket to be merged (will be closed)
        target_ticket_id: ID of the ticket to merge into
        
    Returns:
        Dictionary indicating success or failure
    """
    try:
        make_freshdesk_request(
            "POST",
            f"/tickets/{target_ticket_id}/merge",
            data={"ids": [source_ticket_id]}
        )
        return {"success": True, "message": f"Ticket {source_ticket_id} merged into {target_ticket_id}"}
    except Exception as e:
        return handle_freshdesk_error(e, "merge", "tickets")


def restore_ticket(ticket_id: int) -> Dict[str, Any]:
    """
    Restore a deleted ticket.
    
    Args:
        ticket_id: ID of the ticket to restore
        
    Returns:
        Dictionary containing the restored ticket details
    """
    try:
        response = make_freshdesk_request("PUT", f"/{ticket_id}/restore")
        return response
    except Exception as e:
        return handle_freshdesk_error(e, "restore", "ticket")


def watch_ticket(ticket_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Watch a ticket.
    
    Args:
        ticket_id: ID of the ticket to watch
        user_id: ID of the user to watch the ticket (defaults to authenticated user)
        
    Returns:
        Dictionary indicating success or failure
    """
    try:
        data = {}
        if user_id:
            data["user_id"] = user_id
            
        make_freshdesk_request(
            "POST",
            f"/tickets/{ticket_id}/watch",
            data=data
        )
        return {"success": True, "message": f"Now watching ticket {ticket_id}"}
    except Exception as e:
        return handle_freshdesk_error(e, "watch", "ticket")


def unwatch_ticket(ticket_id: int) -> Dict[str, Any]:
    """
    Unwatch a ticket.
    
    Args:
        ticket_id: ID of the ticket to unwatch
    Returns:
        Dictionary indicating success or failure
    """
    try:
        make_freshdesk_request("PUT", f"/tickets/{ticket_id}/unwatch")
        return {"success": True, "message": f"Stopped watching ticket {ticket_id}"}
    except Exception as e:
        return handle_freshdesk_error(e, "unwatch", "ticket")


def forward_ticket(
    ticket_id: int,
    to_emails: List[str],
    cc_emails: Optional[List[str]] = None,
    bcc_emails: Optional[List[str]] = None,
    body: Optional[str] = None,
    subject: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Forward a ticket to additional email addresses.
    
    Args:
        ticket_id: ID of the ticket to forward
        to_emails: List of email addresses to forward to
        cc_emails: Optional list of CC email addresses
        bcc_emails: Optional list of BCC email addresses
        body: Custom message to include in the forward
        subject: Custom subject for the forwarded email
        **kwargs: Additional parameters for the forward
        
    Returns:
        Dictionary indicating success or failure
    """
    try:
        data = {
            "to_emails": to_emails,
        }
        
        if cc_emails:
            data["cc_emails"] = cc_emails
        if bcc_emails:
            data["bcc_emails"] = bcc_emails
        if body:
            data["body"] = body
        if subject:
            data["subject"] = subject
            
        data.update(kwargs)
        
        make_freshdesk_request(
            "POST",
            f"/tickets/{ticket_id}/forward",
            data={"email": data}
        )
        return {"success": True, "message": f"Ticket {ticket_id} forwarded successfully"}
    except Exception as e:
        return handle_freshdesk_error(e, "forward", "ticket")


def get_archived_ticket(ticket_id: int) -> Dict[str, Any]:
    """
    Retrieve an archived ticket by its ID.
    
    Args:
        ticket_id: ID of the archived ticket to retrieve
        
    Returns:
        Dictionary containing the archived ticket details
    """
    try:
        response = make_freshdesk_request("GET", f"/tickets/archived/{ticket_id}")
        return response
    except Exception as e:
        return handle_freshdesk_error(e, "retrieve", "archived ticket")


def delete_archived_ticket(ticket_id: int) -> Dict[str, Any]:
    """
    Permanently delete an archived ticket.
    
    Args:
        ticket_id: ID of the archived ticket to delete
        
    Returns:
        Dictionary indicating success or failure
    """
    try:
        make_freshdesk_request("DELETE", f"/tickets/archived/{ticket_id}")
        return {"success": True, "message": f"Archived ticket {ticket_id} deleted successfully"}
    except Exception as e:
        return handle_freshdesk_error(e, "delete", "archived ticket")
