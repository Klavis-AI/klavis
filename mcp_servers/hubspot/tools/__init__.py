"""
HubSpot MCP Server Tools Module.

This module provides sanitized tools for interacting with HubSpot CRM.
All responses are validated through Klavis-defined Pydantic schemas, and all errors are sanitized.
"""

from .base import (
    auth_token_context,
    get_hubspot_client,
    safe_api_call,
)

from .errors import (
    KlavisError,
    KlavisErrorCode,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    ValidationError,
    RateLimitError,
    ServiceUnavailableError,
    OperationError,
    sanitize_exception,
    format_error_response,
)

from .schemas import (
    # Base
    KlavisBaseModel,
    # Contact schemas
    Contact,
    ContactList,
    ContactProperties,
    # Company schemas
    Company,
    CompanyList,
    CompanyProperties,
    # Deal schemas
    Deal,
    DealList,
    DealProperties,
    # Ticket schemas
    Ticket,
    TicketList,
    TicketProperties,
    # Task schemas
    Task,
    TaskList,
    TaskProperties,
    # Note schemas
    Note,
    NoteProperties,
    # Property schemas
    PropertyDefinition,
    PropertyList,
    # Association schemas
    AssociationType,
    AssociationRecord,
    AssociationResult,
    AssociationCreateResult,
    BatchAssociationResult,
    # Search schemas
    SearchResults,
    SearchResultItem,
    # Operation results
    OperationResult,
    CreateResult,
    UpdateResult,
    DeleteResult,
)

from .properties import (
    hubspot_list_properties,
    hubspot_search_by_property,
    hubspot_create_property,
)

from .contacts import (
    hubspot_get_contacts,
    hubspot_get_contact_by_id,
    hubspot_delete_contact_by_id,
    hubspot_create_contact,
    hubspot_update_contact_by_id,
)

from .companies import (
    hubspot_get_companies,
    hubspot_get_company_by_id,
    hubspot_create_companies,
    hubspot_update_company_by_id,
    hubspot_delete_company_by_id,
)

from .deals import (
    hubspot_get_deals,
    hubspot_get_deal_by_id,
    hubspot_create_deal,
    hubspot_update_deal_by_id,
    hubspot_delete_deal_by_id,
)

from .tickets import (
    hubspot_get_tickets,
    hubspot_get_ticket_by_id,
    hubspot_create_ticket,
    hubspot_update_ticket_by_id,
    hubspot_delete_ticket_by_id,
)

from .notes import (
    hubspot_create_note,
)

from .tasks import (
    hubspot_get_tasks,
    hubspot_get_task_by_id,
    hubspot_create_task,
    hubspot_update_task_by_id,
    hubspot_delete_task_by_id,
)

from .associations import (
    hubspot_create_association,
    hubspot_delete_association,
    hubspot_get_associations,
    hubspot_batch_create_associations,
)

__all__ = [
    # Base
    "auth_token_context",
    "get_hubspot_client",
    "safe_api_call",
    
    # Errors
    "KlavisError",
    "KlavisErrorCode",
    "AuthenticationError",
    "AuthorizationError",
    "ResourceNotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServiceUnavailableError",
    "OperationError",
    "sanitize_exception",
    "format_error_response",
    
    # Schemas
    "KlavisBaseModel",
    "Contact",
    "ContactList",
    "ContactProperties",
    "Company",
    "CompanyList",
    "CompanyProperties",
    "Deal",
    "DealList",
    "DealProperties",
    "Ticket",
    "TicketList",
    "TicketProperties",
    "Task",
    "TaskList",
    "TaskProperties",
    "Note",
    "NoteProperties",
    "PropertyDefinition",
    "PropertyList",
    "AssociationType",
    "AssociationRecord",
    "AssociationResult",
    "AssociationCreateResult",
    "BatchAssociationResult",
    "SearchResults",
    "SearchResultItem",
    "OperationResult",
    "CreateResult",
    "UpdateResult",
    "DeleteResult",

    # Properties
    "hubspot_list_properties",
    "hubspot_search_by_property",
    "hubspot_create_property",

    # Contacts
    "hubspot_get_contacts",
    "hubspot_get_contact_by_id",
    "hubspot_delete_contact_by_id",
    "hubspot_create_contact",
    "hubspot_update_contact_by_id",

    # Companies
    "hubspot_get_companies",
    "hubspot_get_company_by_id",
    "hubspot_create_companies",
    "hubspot_update_company_by_id",
    "hubspot_delete_company_by_id",

    # Deals
    "hubspot_get_deals",
    "hubspot_get_deal_by_id",
    "hubspot_create_deal",
    "hubspot_update_deal_by_id",
    "hubspot_delete_deal_by_id",

    # Tickets
    "hubspot_get_tickets",
    "hubspot_get_ticket_by_id",
    "hubspot_create_ticket",
    "hubspot_update_ticket_by_id",
    "hubspot_delete_ticket_by_id",
    
    # Notes
    "hubspot_create_note",

    # Tasks
    "hubspot_get_tasks",
    "hubspot_get_task_by_id",
    "hubspot_create_task",
    "hubspot_update_task_by_id",
    "hubspot_delete_task_by_id",

    # Associations
    "hubspot_create_association",
    "hubspot_delete_association",
    "hubspot_get_associations",
    "hubspot_batch_create_associations",
]
