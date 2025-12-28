import logging
from typing import Optional, Dict, Any, List
from .base import make_zendesk_request, validate_pagination_params, ZendeskToolExecutionError

logger = logging.getLogger(__name__)

async def list_tickets(
    page: Optional[int] = None,
    per_page: Optional[int] = None,
    status: Optional[str] = None,
    assignee_id: Optional[int] = None,
    requester_id: Optional[int] = None,
    organization_id: Optional[int] = None
) -> Dict[str, Any]:
    """List tickets with optional filtering and pagination."""
    try:
        params = validate_pagination_params(page, per_page)
        
        # Add optional filters
        if status:
            params["status"] = status
        if assignee_id:
            params["assignee_id"] = assignee_id
        if requester_id:
            params["requester_id"] = requester_id
        if organization_id:
            params["organization_id"] = organization_id
        
        return await make_zendesk_request("GET", "/tickets.json", params=params)
    except Exception as e:
        logger.error(f"Error listing tickets: {e}")
        raise

async def get_ticket(ticket_id: int) -> Dict[str, Any]:
    """Get a single ticket by ID."""
    try:
        if not ticket_id or ticket_id <= 0:
            raise ZendeskToolExecutionError("Valid ticket ID is required")
        
        return await make_zendesk_request("GET", f"/tickets/{ticket_id}.json")
    except Exception as e:
        logger.error(f"Error getting ticket {ticket_id}: {e}")
        raise

async def create_ticket(
    subject: str,
    description: str,
    requester_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None,
    custom_fields: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Create a new ticket."""
    try:
        if not subject or not description:
            raise ZendeskToolExecutionError("Subject and description are required")
        
        ticket_data = {
            "ticket": {
                "subject": subject,
                "description": description
            }
        }
        
        # Add optional fields
        if requester_id:
            ticket_data["ticket"]["requester_id"] = requester_id
        if assignee_id:
            ticket_data["ticket"]["assignee_id"] = assignee_id
        if organization_id:
            ticket_data["ticket"]["organization_id"] = organization_id
        if priority:
            ticket_data["ticket"]["priority"] = priority
        if tags:
            ticket_data["ticket"]["tags"] = tags
        if custom_fields:
            ticket_data["ticket"]["custom_fields"] = custom_fields
        
        return await make_zendesk_request("POST", "/tickets.json", data=ticket_data)
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        raise

async def update_ticket(
    ticket_id: int,
    subject: Optional[str] = None,
    description: Optional[str] = None,
    assignee_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None,
    custom_fields: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Update an existing ticket."""
    try:
        if not ticket_id or ticket_id <= 0:
            raise ZendeskToolExecutionError("Valid ticket ID is required")
        
        ticket_data = {"ticket": {}}
        
        # Add only provided fields
        if subject is not None:
            ticket_data["ticket"]["subject"] = subject
        if description is not None:
            ticket_data["ticket"]["description"] = description
        if assignee_id is not None:
            ticket_data["ticket"]["assignee_id"] = assignee_id
        if status is not None:
            ticket_data["ticket"]["status"] = status
        if priority is not None:
            ticket_data["ticket"]["priority"] = priority
        if tags is not None:
            ticket_data["ticket"]["tags"] = tags
        if custom_fields is not None:
            ticket_data["ticket"]["custom_fields"] = custom_fields
        
        return await make_zendesk_request("PUT", f"/tickets/{ticket_id}.json", data=ticket_data)
    except Exception as e:
        logger.error(f"Error updating ticket {ticket_id}: {e}")
        raise

async def delete_ticket(ticket_id: int) -> Dict[str, Any]:
    """Delete a ticket."""
    try:
        if not ticket_id or ticket_id <= 0:
            raise ZendeskToolExecutionError("Valid ticket ID is required")
        
        return await make_zendesk_request("DELETE", f"/tickets/{ticket_id}.json")
    except Exception as e:
        logger.error(f"Error deleting ticket {ticket_id}: {e}")
        raise

async def add_ticket_comment(
    ticket_id: int,
    comment_body: str,
    public: bool = True,
    author_id: Optional[int] = None
) -> Dict[str, Any]:
    """Add a comment to a ticket."""
    try:
        if not ticket_id or ticket_id <= 0:
            raise ZendeskToolExecutionError("Valid ticket ID is required")
        if not comment_body:
            raise ZendeskToolExecutionError("Comment body is required")
        
        comment_data = {
            "ticket": {
                "comment": {
                    "body": comment_body,
                    "public": public
                }
            }
        }
        
        if author_id:
            comment_data["ticket"]["comment"]["author_id"] = author_id
        
        return await make_zendesk_request("PUT", f"/tickets/{ticket_id}.json", data=comment_data)
    except Exception as e:
        logger.error(f"Error adding comment to ticket {ticket_id}: {e}")
        raise

async def get_ticket_comments(
    ticket_id: int,
    page: Optional[int] = None,
    per_page: Optional[int] = None
) -> Dict[str, Any]:
    """Get comments for a specific ticket."""
    try:
        if not ticket_id or ticket_id <= 0:
            raise ZendeskToolExecutionError("Valid ticket ID is required")
        
        params = validate_pagination_params(page, per_page)
        return await make_zendesk_request("GET", f"/tickets/{ticket_id}/comments.json", params=params)
    except Exception as e:
        logger.error(f"Error getting comments for ticket {ticket_id}: {e}")
        raise

async def assign_ticket(ticket_id: int, assignee_id: int) -> Dict[str, Any]:
    """Assign a ticket to a specific agent."""
    try:
        if not ticket_id or ticket_id <= 0:
            raise ZendeskToolExecutionError("Valid ticket ID is required")
        if not assignee_id or assignee_id <= 0:
            raise ZendeskToolExecutionError("Valid assignee ID is required")
        
        ticket_data = {
            "ticket": {
                "assignee_id": assignee_id
            }
        }
        
        return await make_zendesk_request("PUT", f"/tickets/{ticket_id}.json", data=ticket_data)
    except Exception as e:
        logger.error(f"Error assigning ticket {ticket_id} to {assignee_id}: {e}")
        raise

async def change_ticket_status(ticket_id: int, status: str) -> Dict[str, Any]:
    """Change the status of a ticket."""
    try:
        if not ticket_id or ticket_id <= 0:
            raise ZendeskToolExecutionError("Valid ticket ID is required")
        if not status:
            raise ZendeskToolExecutionError("Status is required")
        
        valid_statuses = ["new", "open", "pending", "hold", "solved", "closed"]
        if status not in valid_statuses:
            raise ZendeskToolExecutionError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        ticket_data = {
            "ticket": {
                "status": status
            }
        }
        
        return await make_zendesk_request("PUT", f"/tickets/{ticket_id}.json", data=ticket_data)
    except Exception as e:
        logger.error(f"Error changing status of ticket {ticket_id} to {status}: {e}")
        raise

async def search_tickets(query: str, page: Optional[int] = None, per_page: Optional[int] = None) -> Dict[str, Any]:
    """Search tickets using Zendesk search syntax."""
    try:
        if not query:
            raise ZendeskToolExecutionError("Search query is required")
        
        params = validate_pagination_params(page, per_page)
        params["query"] = query
        
        return await make_zendesk_request("GET", "/search.json", params=params)
    except Exception as e:
        logger.error(f"Error searching tickets with query '{query}': {e}")
        raise
