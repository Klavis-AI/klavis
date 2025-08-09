import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from .base import make_freshdesk_request, handle_freshdesk_error, remove_none_values, handle_freshdesk_attachments

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




async def create_ticket(
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
    responder_id: Optional[int] = None,
    parent_id: Optional[int] = None,
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
        responder_id: ID of the responder
        parent_id: ID of the parent ticket. If provided, the ticket will be created as a child of the parent ticket.
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
            "name": name,
            "tags": tags,
            "custom_fields": custom_fields,
            "cc_emails": cc_emails,
            "responder_id": responder_id,
            "parent_id": parent_id,
            **kwargs
        }

        options = { }

        ticket_type = kwargs.pop("ticket_type", None)

        if ticket_type:
            ticket_data["type"] = ticket_type

        ticket_data = remove_none_values(ticket_data)

        # Handle attachments if provided
        if attachments:
            options["files"] = handle_freshdesk_attachments("attachments[]", attachments)
        
        logger.info(f"Creating ticket with data: {ticket_data}")
        response = await make_freshdesk_request("POST", "/tickets", data=ticket_data, options=options)
        return response
        
    except Exception as e:
        logger.error(f"Failed to create ticket: {str(e)}")
        return handle_freshdesk_error(e, "create", "ticket")



async def create_ticket_with_attachments(
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
    responder_id: Optional[int] = None,
    parent_id: Optional[int] = None,
    **kwargs
): 
    try:
       return await create_ticket(
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
           responder_id=responder_id,
           parent_id=parent_id,
           attachments=attachments,
           **kwargs
       )
    except Exception as e:
        return handle_freshdesk_error(e, "create", "ticket")


async def get_ticket_by_id(ticket_id: int, include: str = None) -> Dict[str, Any]:
    """
    Retrieve a ticket by its ID.
    
    Args:
        ticket_id: ID of the ticket to retrieve
        include: Optional query parameter to include additional data (e.g., 'conversations', 'requester', 'company', 'stats')
        
    Returns:
        Dictionary containing ticket details
    """
    try:
        endpoint = f"/tickets/{ticket_id}"
        if include:
            endpoint += f"?include={include}"
            
        response = await make_freshdesk_request("GET", endpoint)
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "retrieve", "ticket")


async def update_ticket(
    ticket_id: int,
    subject: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[int] = None,
    status: Optional[int] = None,
    tags: Optional[List[str]] = None,
    custom_fields: Optional[Dict[str, Any]] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
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
        attachments: New attachments (if updating)
        custom_fields: Updated custom fields (if any)
        **kwargs: Additional fields to update
        
    Returns:
        Dictionary containing updated ticket details
    """
    try:
        attachments = attachments or []

        update_data = {
            "subject": subject,
            "description": description,
            "priority": priority,
            "status": status,
            "tags": tags,
            "custom_fields": custom_fields,
            **kwargs
        }
        
        update_data = remove_none_values(update_data)
        
        if not update_data:
            raise ValueError("No fields to update")
            
        logger.info(f"Updating ticket {ticket_id} with data: {update_data}")

        options = {}

        if attachments:
            options["files"] = handle_freshdesk_attachments("attachments[]", attachments)

        response = await make_freshdesk_request("PUT", f"/tickets/{ticket_id}", data=update_data, options=options)
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "update", "ticket")


async def delete_ticket(ticket_id: int) -> Dict[str, Any]:
    """
    Delete a ticket.
    
    Args:
        ticket_id: ID of the ticket to delete
        
    Returns:
        Dictionary indicating success or failure
    """
    try:
        endpoint = f"/tickets/{ticket_id}"
            
        await make_freshdesk_request("DELETE", endpoint)
        return {"success": True, "message": f"Ticket {ticket_id} deleted successfully"}
        
    except Exception as e:
        return handle_freshdesk_error(e, "delete", "ticket")



async def delete_multiple_tickets(ticket_ids: List[int]) -> Dict[str, Any]: 
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
        data = {
            "bulk_action":{
                "ids": ticket_ids
            }
        }
        await make_freshdesk_request("POST", endpoint, data=data)
        return {"success": True, "message": f"Tickets {ticket_ids} deleted successfully"}
    except Exception as e:
        return handle_freshdesk_error(e, "delete", "tickets")


async def delete_attachment(attachment_id: int) -> Dict[str, Any]:
    """
    Delete an attachment from a ticket.
    
    Args:
        attachment_id: ID of the attachment to delete
        
    Returns:
        Dictionary indicating success or failure
    """
    try:
        endpoint = f"/attachments/{attachment_id}"
            
        await make_freshdesk_request("DELETE", endpoint)
        return {"success": True, "message": f"Attachment {attachment_id} deleted successfully"}
        
    except Exception as e:
        return handle_freshdesk_error(e, "delete", "attachment")
    

async def list_tickets(
    status: Optional[int] = None,
    priority: Optional[int] = None,
    requester_id: Optional[int] = None,
    agent_id: Optional[int] = None,
    email: Optional[str] = None,
    group_id: Optional[int] = None,
    company_id: Optional[int] = None,
    ticket_type: Optional[str] = None,
    updated_since: Optional[Union[str, datetime]] = None,
    due_by: Optional[Union[str, datetime]] = None,
    page: int = 1,
    per_page: int = 30,
    order_type: Optional[str] = "desc",
    order_by: Optional[str] = "created_at",
    include: Optional[str] = None,
    **filters
) -> Dict[str, Any]:
    """
    List tickets with optional filtering.
    
    Args:
        status: Filter by status (2-5)
        priority: Filter by priority (1-4)
        requester_id: Filter by requester ID
        agent_id: Filter by agent ID (ID of the agent to whom the ticket has been assigned)
        email: Filter by email address
        group_id: Filter by group ID
        company_id: Filter by company ID
        ticket_type: Filter by ticket type
        updated_since: Only return tickets updated since this date (ISO format or datetime object)
        due_by: Only return tickets due by this date (ISO format or datetime object)
        page: Page number (for pagination)
        per_page: Number of results per page (max 100)
        order_type: Order type (asc or desc)
        order_by: Order by (created_at, updated_at, priority, status)
        include: Include additional data (stats, requester, description)
        **filters: Additional filters as keyword arguments
        
    Returns:
        Dictionary containing list of tickets and pagination info
    """
    try:
        params = {
            "status": status,
            "priority": priority,
            "requester_id": requester_id,
            "agent_id": agent_id,
            "email": email,
            "group_id": group_id,
            "company_id": company_id,
            "type": ticket_type,
            "updated_since": updated_since,
            "due_by": due_by,
            "page": page,
            "per_page": min(per_page, 100),
            "order_type": order_type,
            "order_by": order_by,
            "include": include,
            **filters 
        }

        if ticket_type is not None:
            del params["ticket_type"]

        if updated_since is not None:
            if isinstance(updated_since, datetime):
                updated_since = updated_since.isoformat()
            params["updated_since"] = updated_since

        if due_by is not None:
            if isinstance(due_by, datetime):
                due_by = due_by.isoformat()
            params["due_by"] = due_by

        if (params.get("created_since")):
            if isinstance(params.get("created_since"), datetime):
                params["created_since"] = params.get("created_since").isoformat()
        
        params = remove_none_values(params)
        
        response = await make_freshdesk_request(
            "GET", 
            "/tickets", 
            options={"query_params": params}
        )
        
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "list", "tickets")


async def add_note_to_ticket(
    ticket_id: int,
    body: str,
    private: bool = False,
    user_id: Optional[int] = None,
    incoming: Optional[bool] = False,
    notify_emails: Optional[List[str]] = None,
    attachments: Optional[List[Dict[str, Any]]] = None
    
) -> Dict[str, Any]:
    """
    Add a note to a ticket.
    
    Args:
        ticket_id: ID of the ticket
        body: Content of the note
        private: Whether the note is private
        user_id: ID of the agent adding the note (defaults to authenticated user)
        incoming: Whether the note is incoming
        notify_emails: List of email addresses to notify
        attachments: List of attachments to add to the note
        
    Returns:
        Dictionary containing the created note details
    """
    try:
        note_data = {
            "body": body,
            "private": private,
            "incoming": incoming,
            "notify_emails": notify_emails,
            "user_id": user_id,
        }
        
        note_data = remove_none_values(note_data)
            
        options = {}

        if attachments:
            options["files"] = handle_freshdesk_attachments("attachments[]", attachments)

        response = await make_freshdesk_request(
            "POST",
            f"/tickets/{ticket_id}/notes",
            data=note_data,
            options=options
        )
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "add_note_to", "ticket")


async def reply_to_a_ticket(
    ticket_id: int,
    body: str,
    user_id: Optional[int] = None,
    cc_emails: Optional[List[str]] = None,
    bcc_emails: Optional[List[str]] = None,
    from_email: Optional[str] = None,
    attachments: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Reply to a ticket.
    
    Args:
        ticket_id: ID of the ticket
        body: Content of the reply
        user_id: ID of the agent replying (defaults to authenticated user)
        cc_emails: List of email addresses to CC
        bcc_emails: List of email addresses to BCC
        attachments: List of attachments to add to the reply
        from_email: Email address to use as the sender
        
    Returns:
        Dictionary containing the created reply details
    """
    try:
        data = {
            "body": body,
            "user_id": user_id,
            "cc_emails": cc_emails or [],
            "bcc_emails": bcc_emails or [],
            "from_email": from_email
        }
        
        data = remove_none_values(data)
            
        options = {}

        if attachments:
            options["files"] = handle_freshdesk_attachments("attachments[]", attachments)

        response = await make_freshdesk_request(
            "POST",
            f"/tickets/{ticket_id}/reply",
            data=data,
            options=options
        )
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "reply_to", "ticket")


async def update_note(
    note_id: int,
    body: str,
    attachments: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Update a note or reply to a ticket.
    
    Args:
        note_id: ID of the note
        body: Content of the note
        attachments: List of attachments to add to the note
        
    Returns:
        Dictionary containing the updated note details
    """
    try:
        note_data = {
            "body": body,
        }
        
        note_data = remove_none_values(note_data)
            
        options = {}

        if attachments:
            options["files"] = handle_freshdesk_attachments("attachments[]", attachments)

        response = await make_freshdesk_request(
            "PUT",
            f"/conversations/{note_id}",
            data=note_data,
            options=options
        )
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "update", "note")


async def delete_note(
    note_id: int,
) -> Dict[str, Any]:
    """
    Delete a note or reply to a ticket.
    
    Args:
        note_id: ID of the note
        
    Returns:
        Dictionary containing the deleted note details
    """
    try:
        response = await make_freshdesk_request(
            "DELETE",
            f"/conversations/{note_id}",
        )
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "delete", "note")


async def filter_tickets(
    query: str,
    page: int = 1,
    per_page: int = 30
) -> Dict[str, Any]:
    """
    Filter tickets using a query string.
    
    Args:
        query: Filter query string (e.g., "priority:3 AND status:2 OR priority:4")
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
        
        response = await make_freshdesk_request(
            "GET",
            "/search/tickets",
            options={"query_params": params}
        )
        
        return response
        
    except Exception as e:
        return handle_freshdesk_error(e, "filter", "tickets")



async def merge_tickets(
    primary_ticket_id: int, 
    ticket_ids: List[int], 
    convert_recepients_to_cc: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Merge two tickets.
    
    Args:
        primary_ticket_id: ID of the ticket to be merged (will be closed)
        ticket_ids: List of IDs of tickets to merge into the primary ticket
        
    Returns:
        Dictionary indicating success or failure
    """
    try:

        merge_data = {
            "primary_id": primary_ticket_id,
            "ticket_ids": ticket_ids,
            "convert_recepients_to_cc": convert_recepients_to_cc
        }

        merge_data = remove_none_values(merge_data)

        await make_freshdesk_request(
            "PUT",
            f"/tickets/merge",
            data=merge_data
        )
        return {"success": True, "message": f"Ticket {primary_ticket_id} merged into {ticket_ids}"}
    except Exception as e:
        return handle_freshdesk_error(e, "merge", "tickets")


async def restore_ticket(ticket_id: int) -> Dict[str, Any]:
    """
    Restore a deleted ticket.
    
    Args:
        ticket_id: ID of the ticket to restore
        
    Returns:
        Dictionary containing the restored ticket details
    """
    try:
        response = await make_freshdesk_request("PUT", f"/tickets/{ticket_id}/restore")
        return response
    except Exception as e:
        return handle_freshdesk_error(e, "restore", "ticket")


async def watch_ticket(ticket_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Watch a ticket.
    
    Args:
        ticket_id: ID of the ticket to watch
        user_id: ID of the user to watch the ticket (defaults to authenticated user)
        
    Returns:
        Dictionary indicating success or failure
    """
    try:
        data = {
            "user_id": user_id
        }

        data = remove_none_values(data)
        
        await make_freshdesk_request(
            "POST",
            f"/tickets/{ticket_id}/watch",
            data=data
        )
        return {"success": True, "message": f"Now watching ticket {ticket_id}"}
    except Exception as e:
        return handle_freshdesk_error(e, "watch", "ticket")


async def unwatch_ticket(ticket_id: int) -> Dict[str, Any]:
    """
    Unwatch a ticket.
    
    Args:
        ticket_id: ID of the ticket to unwatch
    Returns:
        Dictionary indicating success or failure
    """
    try:
        await make_freshdesk_request("PUT", f"/tickets/{ticket_id}/unwatch")
        return {"success": True, "message": f"Stopped watching ticket {ticket_id}"}
    except Exception as e:
        return handle_freshdesk_error(e, "unwatch", "ticket")


async def forward_ticket(
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
            "cc_emails": cc_emails,
            "bcc_emails": bcc_emails,
            "body": body,
            "subject": subject,
            **kwargs
        }
        
        data = remove_none_values(data)
    
        await make_freshdesk_request(
            "POST",
            f"/tickets/{ticket_id}/forward",
            data=data
        )
        return {"success": True, "message": f"Ticket {ticket_id} forwarded successfully"}
    except Exception as e:
        return handle_freshdesk_error(e, "forward", "ticket")


async def get_archived_ticket(ticket_id: int) -> Dict[str, Any]:
    """
    Retrieve an archived ticket by its ID.
    
    Args:
        ticket_id: ID of the archived ticket to retrieve
        
    Returns:
        Dictionary containing the archived ticket details
    """
    try:
        response = await make_freshdesk_request("GET", f"/tickets/archived/{ticket_id}")
        return response
    except Exception as e:
        return handle_freshdesk_error(e, "retrieve", "archived ticket")


async def delete_archived_ticket(ticket_id: int) -> Dict[str, Any]:
    """
    Permanently delete an archived ticket.
    
    Args:
        ticket_id: ID of the archived ticket to delete
        
    Returns:
        Dictionary indicating success or failure
    """
    try:
        await make_freshdesk_request("DELETE", f"/tickets/archived/{ticket_id}")
        return {"success": True, "message": f"Archived ticket {ticket_id} deleted successfully"}
    except Exception as e:
        return handle_freshdesk_error(e, "delete", "archived ticket")
