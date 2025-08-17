import logging
from typing import Any, Dict, List, Optional
import mimetypes
import os
from .base import make_freshdesk_request, handle_freshdesk_error, remove_none_values

# Configure logging
logger = logging.getLogger(__name__)

# Contact status constants
CONTACT_STATUS_VERIFIED = "verified"
CONTACT_STATUS_UNVERIFIED = "unverified"
CONTACT_STATUS_BLOCKED = "blocked"
CONTACT_STATUS_DELETED = "deleted"

async def create_contact(
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    mobile: Optional[str] = None,
    company_id: Optional[int] = None,
    description: Optional[str] = None,
    job_title: Optional[str] = None,
    tags: Optional[List[str]] = None,
    custom_fields: Optional[Dict[str, Any]] = None,
    avatar_path: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a new contact in Freshdesk.
    
    Args:
        name: Name of the contact
        email: Primary email address
        phone: Telephone number
        mobile: Mobile number
        company_id: ID of the primary company
        description: Description of the contact
        job_title: Job title
        tags: List of tags
        custom_fields: Dictionary of custom field values
        avatar_path: Path to avatar image file
        **kwargs: Additional contact fields
        
    Returns:
        Dict containing the created contact data or error information
    """
    if not any([email, phone, mobile]):
        return {"error": "At least one of email, phone, or mobile is required"}
    
    contact_data = {
        "name": name,
        "email": email,
        "phone": phone,
        "mobile": mobile,
        "company_id": company_id,
        "description": description,
        "job_title": job_title,
        "tags": tags,
        "custom_fields": custom_fields,
        **kwargs
    }
    
    contact_data = remove_none_values(contact_data)

    options = { }
    
    try:
        if avatar_path:
            options["files"] = handle_freshdesk_attachments("avatar", [{"type": "local", "content": avatar_path, "name": os.path.basename(avatar_path), "media_type": mimetypes.guess_type(avatar_path)[0]}])
    
        return await make_freshdesk_request("POST", "/contacts", data=contact_data, options=options)
    except Exception as e:
        return handle_freshdesk_error(e, "create", "contact")

async def get_contact_by_id(contact_id: int) -> Dict[str, Any]:
    """
    Retrieve a contact by ID.
    
    Args:
        contact_id: ID of the contact to retrieve
        
    Returns:
        Dict containing the contact data or error information
    """
    try:
        return await make_freshdesk_request("GET", f"/contacts/{contact_id}")
    except Exception as e:
        return handle_freshdesk_error(e, "retrieve", "contact")

async def list_contacts(
    email: Optional[str] = None,
    phone: Optional[str] = None,
    mobile: Optional[str] = None,
    company_id: Optional[int] = None,
    state: Optional[str] = None,
    updated_since: Optional[str] = None,
    page: int = 1,
    per_page: int = 30
) -> Dict[str, Any]:
    """
    List all contacts, optionally filtered by parameters.
    
    Args:
        email: Filter by email
        phone: Filter by phone number
        mobile: Filter by mobile number
        company_id: Filter by company ID
        state: Filter by state (verified, unverified, blocked, deleted)
        updated_since: Filter by last updated date (ISO 8601 format)
        page: Page number (1-based)
        per_page: Number of results per page (1-100)
        
    Returns:
        Dict containing the list of contacts and pagination info
    """
    params = {
        "email": email,
        "phone": phone,
        "mobile": mobile,
        "company_id": company_id,
        "state": state,
        "updated_since": updated_since,
        "page": page,
        "per_page": min(per_page, 100) 
    }
    
    params = remove_none_values(params)
    
    try:
        return await make_freshdesk_request("GET", "/contacts", options={"query_params": params})
    except Exception as e:
        return handle_freshdesk_error(e, "list", "contacts")


async def update_contact(
    contact_id: int,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    mobile: Optional[str] = None,
    company_id: Optional[int] = None,
    description: Optional[str] = None,
    job_title: Optional[str] = None,
    tags: Optional[List[str]] = None,
    custom_fields: Optional[Dict[str, Any]] = None,
    avatar_path: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Update an existing contact.
    
    Args:
        contact_id: ID of the contact to update
        name: New name
        email: New primary email
        phone: New phone number
        mobile: New mobile number
        company_id: New company ID
        description: New description
        job_title: New job title
        tags: Updated list of tags
        custom_fields: Updated custom fields
        avatar_path: Path to new avatar image file
        **kwargs: Additional contact fields to update
        
    Returns:
        Dict containing the updated contact data or error information
    """
    contact_data = {
        "name": name,
        "email": email,
        "phone": phone,
        "mobile": mobile,
        "company_id": company_id,
        "description": description,
        "job_title": job_title,
        "tags": tags,
        "custom_fields": custom_fields,
        **kwargs
    }
    
    contact_data = remove_none_values(contact_data)

    if not contact_data:
        raise ValueError("No fields to update")

    options = {}
    
    try:
        if avatar_path:
            options["files"] = handle_freshdesk_attachments("avatar", [{"type": "local", "content": avatar_path, "name": os.path.basename(avatar_path), "media_type": mimetypes.guess_type(avatar_path)[0]}])
           
        return await make_freshdesk_request("PUT", f"/contacts/{contact_id}", data=contact_data, options=options)
        
    except Exception as e:
        return handle_freshdesk_error(e, "update", "contact")



async def delete_contact(
    contact_id: int, 
    hard_delete: bool = False, 
    force: bool = False
) -> Dict[str, Any]:
    """
    Delete a contact.
    
    Args:
        contact_id: ID of the contact to delete
        hard_delete: If True, permanently delete the contact
        force: If True, force hard delete even if not soft deleted first
        
    Returns:
        Dict with success status or error information
    """
    try:
        if hard_delete:
            return await make_freshdesk_request(
                "DELETE", 
                f"/contacts/{contact_id}/hard_delete?force={str(force).lower()}"
            )
        else:
            return await make_freshdesk_request("DELETE", f"/contacts/{contact_id}")
    except Exception as e:
        return handle_freshdesk_error(e, "delete", "contact")


async def filter_contacts(
    query: str,
    page: int = 1,
    updated_since: Optional[str] = None
) -> Dict[str, Any]:
    """
    Filter contacts using a query string.
    
    Args:
        query: Filter query string (e.g., "priority:3 AND status:2 OR priority:4")
        page: Page number (1-based)
        updated_since: Filter by last updated date (ISO 8601 format)
        
    Returns:
        Dict containing search results and pagination info
    """
    params = {
        "query": f"'{query}'",
        "page": page,
        "updated_since": updated_since
    }
    
    params = remove_none_values(params)
    
    try:
        return await make_freshdesk_request("GET", "/search/contacts", options={"query_params": params})
    except Exception as e:
        return handle_freshdesk_error(e, "filter", "contacts")

async def search_contacts_by_name(name: str) -> Dict[str, Any]:
    """
    Search contacts by name for autocomplete.
    
    Args:
        name: Search term (contact name or part of name)
        
    Returns:
        List of matching contacts with basic info
    """
    try:
        return await make_freshdesk_request("GET", "/contacts/autocomplete", options={"query_params": {"term": name}})
    except Exception as e:
        return handle_freshdesk_error(e, "search", "contacts")

async def make_contact_agent(
    contact_id: int,
    occasional: bool = False,
    signature: Optional[str] = None,
    ticket_scope: int = 1,
    skill_ids: Optional[List[int]] = None,
    group_ids: Optional[List[int]] = None,
    role_ids: Optional[List[int]] = None,
    agent_type: str = "support_agent",
    focus_mode: bool = True
) -> Dict[str, Any]:
    """
    Convert a contact to an agent.
    
    Args:
        contact_id: ID of the contact to convert
        occasional: Whether agent is occasional
        signature: HTML signature for the agent
        ticket_scope: Ticket permission level (1=Global, 2=Group, 3=Restricted)
        skill_ids: List of skill IDs
        group_ids: List of group IDs
        role_ids: List of role IDs
        agent_type: Type of agent (support_agent, field_agent, collaborator)
        focus_mode: Whether focus mode is enabled
        
    Returns:
        Dict containing the agent data or error information
    """
    agent_data = {
        "occasional": occasional,
        "signature": signature,
        "ticket_scope": ticket_scope,
        "skill_ids": skill_ids or [],
        "group_ids": group_ids or [],
        "role_ids": role_ids or [],
        "type": agent_type,
        "focus_mode": focus_mode
    }
    
    agent_data = remove_none_values(agent_data)
    
    try:
        return await make_freshdesk_request(
            "PUT",
            f"/contacts/{contact_id}/make_agent",
            data=agent_data
        )
    except Exception as e:
        return handle_freshdesk_error(e, "create", "contact_agent")

async def restore_contact(contact_id: int) -> Dict[str, Any]:
    """
    Restore a soft-deleted contact.
    
    Args:
        contact_id: ID of the contact to restore
        
    Returns:
        Dict with success status or error information
    """
    try:
        return await make_freshdesk_request(
            "PUT",
            f"/contacts/{contact_id}/restore"
        )
    except Exception as e:
        return handle_freshdesk_error(e, "restore", "contact")

async def send_contact_invite(contact_id: int) -> Dict[str, Any]:
    """
    Send an activation email to a contact.
    
    Args:
        contact_id: ID of the contact to invite
        
    Returns:
        Dict with success status or error information
    """
    try:
        return await make_freshdesk_request(
            "POST",
            f"/contacts/{contact_id}/send_invite"
        )
    except Exception as e:
        return handle_freshdesk_error(e, "send", "contact_invite")

async def merge_contacts(
    primary_contact_id: int,
    secondary_contact_ids: List[int],
    contact_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Merge multiple contacts into a primary contact.
    
    Args:
        primary_contact_id: ID of the contact to merge into
        secondary_contact_ids: List of contact IDs to merge
        contact_data: Optional dictionary of fields to update on the primary contact
        
    Returns:
        Dict with success status or error information
    """
    if not secondary_contact_ids:
        raise ValueError("At least one secondary contact ID is required")
    
    merge_data = {
        "primary_contact_id": primary_contact_id,
        "secondary_contact_ids": secondary_contact_ids,
        "contact": contact_data or {}
    }
    
    try:
        return await make_freshdesk_request(
            "PUT",
            f"/contacts/merge",
            data=merge_data
        )
    except Exception as e:
        return handle_freshdesk_error(e, "merge", "contacts")