# Zendesk MCP Server Tools

from .base import ZendeskToolExecutionError, auth_token_context, auth_email_context
from .tickets import (
    list_tickets,
    get_ticket,
    create_ticket,
    update_ticket,
    delete_ticket,
    add_ticket_comment,
    get_ticket_comments,
    assign_ticket,
    change_ticket_status,
    search_tickets
)
from .users import (
    list_users,
    get_user,
    create_user,
    update_user,
    delete_user,
    search_users,
    get_user_tickets,
    get_user_organizations,
    suspend_user,
    reactivate_user,
    get_current_user
)
from .organizations import (
    list_organizations,
    get_organization,
    create_organization,
    update_organization,
    delete_organization,
    search_organizations,
    get_organization_tickets,
    get_organization_users
)

__all__ = [
    # Base
    "ZendeskToolExecutionError",
    "auth_token_context",
    "auth_email_context",
    
    # Tickets
    "list_tickets",
    "get_ticket",
    "create_ticket",
    "update_ticket",
    "delete_ticket",
    "add_ticket_comment",
    "get_ticket_comments",
    "assign_ticket",
    "change_ticket_status",
    "search_tickets",
    
    # Users
    "list_users",
    "get_user",
    "create_user",
    "update_user",
    "delete_user",
    "search_users",
    "get_user_tickets",
    "get_user_organizations",
    "suspend_user",
    "reactivate_user",
    "get_current_user",
    
    # Organizations
    "list_organizations",
    "get_organization",
    "create_organization",
    "update_organization",
    "delete_organization",
    "search_organizations",
    "get_organization_tickets",
    "get_organization_users",
]
