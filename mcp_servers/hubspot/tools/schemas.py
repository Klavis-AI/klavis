"""
Klavis-defined Pydantic schemas for HubSpot MCP server.

These schemas define the Klavis Interface - all data returned to the LLM
must conform to these schemas. Raw third-party API responses are never
exposed directly.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# =============================================================================
# Helper Functions
# =============================================================================

def _to_iso_string(value: Any) -> Optional[str]:
    """
    Convert a datetime or string value to ISO format string.
    
    HubSpot API returns timestamps as datetime objects, but we normalize
    them to ISO format strings for consistent JSON serialization.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        return value
    # Fallback: convert to string
    return str(value)


def _to_dict_safe(obj: Any) -> Dict[str, Any]:
    """
    Safely convert an object to a dictionary.
    
    Handles HubSpot API objects that have a to_dict() method,
    dict-like objects, and plain dicts.
    """
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    # HubSpot SDK objects typically have to_dict() method
    if hasattr(obj, 'to_dict') and callable(obj.to_dict):
        return obj.to_dict()
    # Fallback for objects with __dict__
    if hasattr(obj, '__dict__'):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
    return {}


# =============================================================================
# Base Schemas
# =============================================================================

class KlavisBaseModel(BaseModel):
    """Base model for all Klavis schemas with common configuration."""
    
    class Config:
        # Allow extra fields to be ignored when parsing, but don't include them in output
        extra = "ignore"
        # Validate on assignment
        validate_assignment = True


class KlavisTimestamps(KlavisBaseModel):
    """Standard timestamp fields for HubSpot objects."""
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO format)")
    updated_at: Optional[str] = Field(None, description="Last update timestamp (ISO format)")


# =============================================================================
# Contact Schemas
# =============================================================================

class ContactProperties(KlavisBaseModel):
    """Klavis-normalized contact properties."""
    email: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    phone: Optional[str] = None
    mobilephone: Optional[str] = None
    company: Optional[str] = None
    jobtitle: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    lifecyclestage: Optional[str] = None
    hs_lead_status: Optional[str] = None
    hubspot_owner_id: Optional[str] = None
    # Allow additional custom properties
    additional_properties: Optional[Dict[str, Any]] = Field(default_factory=dict)


class Contact(KlavisBaseModel):
    """Klavis-normalized contact record."""
    id: str = Field(..., description="Unique contact identifier")
    properties: ContactProperties
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO format)")
    updated_at: Optional[str] = Field(None, description="Last update timestamp (ISO format)")
    archived: bool = Field(False, description="Whether the contact is archived")


class ContactList(KlavisBaseModel):
    """Klavis-normalized list of contacts."""
    contacts: List[Contact] = Field(default_factory=list)
    total: int = 0
    has_more: bool = False


# =============================================================================
# Company Schemas
# =============================================================================

class CompanyProperties(KlavisBaseModel):
    """Klavis-normalized company properties."""
    name: Optional[str] = None
    domain: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    numberofemployees: Optional[str] = None
    industry: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    annualrevenue: Optional[str] = None
    timezone: Optional[str] = None
    lifecyclestage: Optional[str] = None
    hs_lead_status: Optional[str] = None
    additional_properties: Optional[Dict[str, Any]] = Field(default_factory=dict)


class Company(KlavisBaseModel):
    """Klavis-normalized company record."""
    id: str = Field(..., description="Unique company identifier")
    properties: CompanyProperties
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO format)")
    updated_at: Optional[str] = Field(None, description="Last update timestamp (ISO format)")
    archived: bool = Field(False, description="Whether the company is archived")


class CompanyList(KlavisBaseModel):
    """Klavis-normalized list of companies."""
    companies: List[Company] = Field(default_factory=list)
    total: int = 0
    has_more: bool = False


# =============================================================================
# Deal Schemas
# =============================================================================

class DealProperties(KlavisBaseModel):
    """Klavis-normalized deal properties."""
    dealname: Optional[str] = None
    amount: Optional[str] = None
    dealstage: Optional[str] = None
    dealstage_label: Optional[str] = None  # Human-readable stage name
    pipeline: Optional[str] = None
    closedate: Optional[str] = None
    hubspot_owner_id: Optional[str] = None
    dealtype: Optional[str] = None
    description: Optional[str] = None
    additional_properties: Optional[Dict[str, Any]] = Field(default_factory=dict)


class Deal(KlavisBaseModel):
    """Klavis-normalized deal record."""
    id: str = Field(..., description="Unique deal identifier")
    properties: DealProperties
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO format)")
    updated_at: Optional[str] = Field(None, description="Last update timestamp (ISO format)")
    archived: bool = Field(False, description="Whether the deal is archived")


class DealList(KlavisBaseModel):
    """Klavis-normalized list of deals."""
    deals: List[Deal] = Field(default_factory=list)
    total: int = 0
    has_more: bool = False


# =============================================================================
# Ticket Schemas
# =============================================================================

class TicketProperties(KlavisBaseModel):
    """Klavis-normalized ticket properties."""
    subject: Optional[str] = None
    content: Optional[str] = None
    hs_pipeline: Optional[str] = None
    hs_pipeline_stage: Optional[str] = None
    hs_ticket_priority: Optional[str] = None
    hubspot_owner_id: Optional[str] = None
    additional_properties: Optional[Dict[str, Any]] = Field(default_factory=dict)


class Ticket(KlavisBaseModel):
    """Klavis-normalized ticket record."""
    id: str = Field(..., description="Unique ticket identifier")
    properties: TicketProperties
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO format)")
    updated_at: Optional[str] = Field(None, description="Last update timestamp (ISO format)")
    archived: bool = Field(False, description="Whether the ticket is archived")


class TicketList(KlavisBaseModel):
    """Klavis-normalized list of tickets."""
    tickets: List[Ticket] = Field(default_factory=list)
    total: int = 0
    has_more: bool = False


# =============================================================================
# Task Schemas
# =============================================================================

class TaskProperties(KlavisBaseModel):
    """Klavis-normalized task properties."""
    hs_task_subject: Optional[str] = None
    hs_task_body: Optional[str] = None
    hs_task_status: Optional[str] = None
    hs_task_priority: Optional[str] = None
    hs_task_type: Optional[str] = None
    hs_timestamp: Optional[str] = None
    hubspot_owner_id: Optional[str] = None
    additional_properties: Optional[Dict[str, Any]] = Field(default_factory=dict)


class Task(KlavisBaseModel):
    """Klavis-normalized task record."""
    id: str = Field(..., description="Unique task identifier")
    properties: TaskProperties
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO format)")
    updated_at: Optional[str] = Field(None, description="Last update timestamp (ISO format)")
    archived: bool = Field(False, description="Whether the task is archived")


class TaskList(KlavisBaseModel):
    """Klavis-normalized list of tasks."""
    tasks: List[Task] = Field(default_factory=list)
    total: int = 0
    has_more: bool = False


# =============================================================================
# Note Schemas
# =============================================================================

class NoteProperties(KlavisBaseModel):
    """Klavis-normalized note properties."""
    hs_note_body: Optional[str] = None
    hs_timestamp: Optional[str] = None
    hubspot_owner_id: Optional[str] = None
    additional_properties: Optional[Dict[str, Any]] = Field(default_factory=dict)


class Note(KlavisBaseModel):
    """Klavis-normalized note record."""
    id: str = Field(..., description="Unique note identifier")
    properties: NoteProperties
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO format)")
    updated_at: Optional[str] = Field(None, description="Last update timestamp (ISO format)")
    archived: bool = Field(False, description="Whether the note is archived")


# =============================================================================
# Property Schemas
# =============================================================================

class PropertyDefinition(KlavisBaseModel):
    """Klavis-normalized property definition."""
    name: str = Field(..., description="Internal property name")
    label: str = Field(..., description="Display label")
    type: str = Field(..., description="Data type")
    field_type: str = Field(..., description="UI field type")


class PropertyList(KlavisBaseModel):
    """Klavis-normalized list of property definitions."""
    properties: List[PropertyDefinition] = Field(default_factory=list)
    object_type: str = Field(..., description="Object type these properties belong to")


# =============================================================================
# Association Schemas
# =============================================================================

class AssociationType(KlavisBaseModel):
    """Association type information."""
    category: Optional[str] = None
    type_id: Optional[int] = None
    label: Optional[str] = None


class AssociationRecord(KlavisBaseModel):
    """Single association record."""
    to_object_id: str
    association_types: List[AssociationType] = Field(default_factory=list)


class AssociationResult(KlavisBaseModel):
    """Result of association query."""
    from_object_type: str
    from_object_id: str
    to_object_type: str
    associations: List[AssociationRecord] = Field(default_factory=list)
    total: int = 0


class AssociationCreateResult(KlavisBaseModel):
    """Result of creating an association."""
    status: str
    message: str
    from_object_type: str
    from_object_id: str
    to_object_type: str
    to_object_id: str


class BatchAssociationResult(KlavisBaseModel):
    """Result of batch association creation."""
    status: str
    total_requested: int
    successful: int
    failed: int
    errors: Optional[List[str]] = None


# =============================================================================
# Search Result Schemas
# =============================================================================

class SearchResultItem(KlavisBaseModel):
    """Generic search result item with normalized properties."""
    id: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class SearchResults(KlavisBaseModel):
    """Klavis-normalized search results."""
    results: List[SearchResultItem] = Field(default_factory=list)
    total: int = 0


# =============================================================================
# Operation Result Schemas
# =============================================================================

class OperationResult(KlavisBaseModel):
    """Standard operation result."""
    status: str = Field(..., description="Operation status: success, error")
    message: str = Field(..., description="Human-readable result message")
    resource_id: Optional[str] = Field(None, description="ID of affected resource if applicable")


class CreateResult(OperationResult):
    """Result of a create operation."""
    pass


class UpdateResult(OperationResult):
    """Result of an update operation."""
    pass


class DeleteResult(OperationResult):
    """Result of a delete operation."""
    pass


# =============================================================================
# Utility Functions for Schema Conversion
# =============================================================================

def extract_standard_properties(
    raw_properties: Dict[str, Any],
    known_fields: List[str]
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Separate known standard properties from additional/custom properties.
    
    Args:
        raw_properties: Raw properties dict from API
        known_fields: List of known standard field names
        
    Returns:
        Tuple of (standard_props, additional_props)
    """
    standard = {}
    additional = {}
    
    for key, value in raw_properties.items():
        if key in known_fields:
            standard[key] = value
        else:
            additional[key] = value
            
    return standard, additional


def normalize_contact(raw_obj: Any) -> Contact:
    """Convert raw HubSpot contact object to Klavis Contact schema."""
    # Extract ID - handle both SDK objects and dicts
    obj_id = getattr(raw_obj, 'id', None)
    if obj_id is None and isinstance(raw_obj, dict):
        obj_id = raw_obj.get('id', '')
    obj_id = str(obj_id) if obj_id else ''
    
    # Extract and convert properties
    raw_props = getattr(raw_obj, 'properties', None)
    if raw_props is None and isinstance(raw_obj, dict):
        raw_props = raw_obj.get('properties', {})
    raw_props = _to_dict_safe(raw_props)
    
    known_fields = [
        'email', 'firstname', 'lastname', 'phone', 'mobilephone', 'company',
        'jobtitle', 'website', 'address', 'city', 'state', 'zip', 'country',
        'lifecyclestage', 'hs_lead_status', 'hubspot_owner_id'
    ]
    
    standard, additional = extract_standard_properties(raw_props, known_fields)
    standard['additional_properties'] = additional
    
    # Extract timestamps - prefer object attributes (datetime), fallback to properties
    created_at = getattr(raw_obj, 'created_at', None) or raw_props.get('createdate')
    updated_at = getattr(raw_obj, 'updated_at', None) or raw_props.get('lastmodifieddate')
    
    # Extract archived status
    archived = getattr(raw_obj, 'archived', False)
    if archived is None:
        archived = False
    
    return Contact(
        id=obj_id,
        properties=ContactProperties(**standard),
        created_at=_to_iso_string(created_at),
        updated_at=_to_iso_string(updated_at),
        archived=archived
    )


def normalize_company(raw_obj: Any) -> Company:
    """Convert raw HubSpot company object to Klavis Company schema."""
    # Extract ID - handle both SDK objects and dicts
    obj_id = getattr(raw_obj, 'id', None)
    if obj_id is None and isinstance(raw_obj, dict):
        obj_id = raw_obj.get('id', '')
    obj_id = str(obj_id) if obj_id else ''
    
    # Extract and convert properties
    raw_props = getattr(raw_obj, 'properties', None)
    if raw_props is None and isinstance(raw_obj, dict):
        raw_props = raw_obj.get('properties', {})
    raw_props = _to_dict_safe(raw_props)
    
    known_fields = [
        'name', 'domain', 'website', 'phone', 'address', 'address2', 'city',
        'state', 'zip', 'country', 'numberofemployees', 'industry', 'type',
        'description', 'annualrevenue', 'timezone', 'lifecyclestage', 'hs_lead_status'
    ]
    
    standard, additional = extract_standard_properties(raw_props, known_fields)
    standard['additional_properties'] = additional
    
    # Extract timestamps
    created_at = getattr(raw_obj, 'created_at', None) or raw_props.get('createdate')
    updated_at = getattr(raw_obj, 'updated_at', None) or raw_props.get('lastmodifieddate')
    
    # Extract archived status
    archived = getattr(raw_obj, 'archived', False)
    if archived is None:
        archived = False
    
    return Company(
        id=obj_id,
        properties=CompanyProperties(**standard),
        created_at=_to_iso_string(created_at),
        updated_at=_to_iso_string(updated_at),
        archived=archived
    )


def normalize_deal(raw_obj: Any, stage_label_map: Optional[Dict[str, str]] = None) -> Deal:
    """Convert raw HubSpot deal object to Klavis Deal schema."""
    # Extract ID - handle both SDK objects and dicts
    obj_id = getattr(raw_obj, 'id', None)
    if obj_id is None and isinstance(raw_obj, dict):
        obj_id = raw_obj.get('id', '')
    obj_id = str(obj_id) if obj_id else ''
    
    # Extract and convert properties
    raw_props = getattr(raw_obj, 'properties', None)
    if raw_props is None and isinstance(raw_obj, dict):
        raw_props = raw_obj.get('properties', {})
    raw_props = _to_dict_safe(raw_props)
    
    known_fields = [
        'dealname', 'amount', 'dealstage', 'dealstage_label', 'pipeline',
        'closedate', 'hubspot_owner_id', 'dealtype', 'description'
    ]
    
    # Enrich with stage label if available
    if stage_label_map:
        stage_id = raw_props.get('dealstage')
        if stage_id and stage_id in stage_label_map:
            raw_props['dealstage_label'] = stage_label_map[stage_id]
    
    standard, additional = extract_standard_properties(raw_props, known_fields)
    standard['additional_properties'] = additional
    
    # Extract timestamps
    created_at = getattr(raw_obj, 'created_at', None) or raw_props.get('createdate')
    updated_at = getattr(raw_obj, 'updated_at', None) or raw_props.get('lastmodifieddate')
    
    # Extract archived status
    archived = getattr(raw_obj, 'archived', False)
    if archived is None:
        archived = False
    
    return Deal(
        id=obj_id,
        properties=DealProperties(**standard),
        created_at=_to_iso_string(created_at),
        updated_at=_to_iso_string(updated_at),
        archived=archived
    )


def normalize_ticket(raw_obj: Any) -> Ticket:
    """Convert raw HubSpot ticket object to Klavis Ticket schema."""
    # Extract ID - handle both SDK objects and dicts
    obj_id = getattr(raw_obj, 'id', None)
    if obj_id is None and isinstance(raw_obj, dict):
        obj_id = raw_obj.get('id', '')
    obj_id = str(obj_id) if obj_id else ''
    
    # Extract and convert properties
    raw_props = getattr(raw_obj, 'properties', None)
    if raw_props is None and isinstance(raw_obj, dict):
        raw_props = raw_obj.get('properties', {})
    raw_props = _to_dict_safe(raw_props)
    
    known_fields = [
        'subject', 'content', 'hs_pipeline', 'hs_pipeline_stage',
        'hs_ticket_priority', 'hubspot_owner_id'
    ]
    
    standard, additional = extract_standard_properties(raw_props, known_fields)
    standard['additional_properties'] = additional
    
    # Extract timestamps
    created_at = getattr(raw_obj, 'created_at', None) or raw_props.get('createdate')
    updated_at = getattr(raw_obj, 'updated_at', None) or raw_props.get('lastmodifieddate')
    
    # Extract archived status
    archived = getattr(raw_obj, 'archived', False)
    if archived is None:
        archived = False
    
    return Ticket(
        id=obj_id,
        properties=TicketProperties(**standard),
        created_at=_to_iso_string(created_at),
        updated_at=_to_iso_string(updated_at),
        archived=archived
    )


def normalize_task(raw_obj: Any) -> Task:
    """Convert raw HubSpot task object to Klavis Task schema."""
    # Extract ID - handle both SDK objects and dicts
    obj_id = getattr(raw_obj, 'id', None)
    if obj_id is None and isinstance(raw_obj, dict):
        obj_id = raw_obj.get('id', '')
    obj_id = str(obj_id) if obj_id else ''
    
    # Extract and convert properties
    raw_props = getattr(raw_obj, 'properties', None)
    if raw_props is None and isinstance(raw_obj, dict):
        raw_props = raw_obj.get('properties', {})
    raw_props = _to_dict_safe(raw_props)
    
    known_fields = [
        'hs_task_subject', 'hs_task_body', 'hs_task_status', 'hs_task_priority',
        'hs_task_type', 'hs_timestamp', 'hubspot_owner_id'
    ]
    
    standard, additional = extract_standard_properties(raw_props, known_fields)
    standard['additional_properties'] = additional
    
    # Extract timestamps
    created_at = getattr(raw_obj, 'created_at', None) or raw_props.get('createdate')
    updated_at = getattr(raw_obj, 'updated_at', None) or raw_props.get('lastmodifieddate')
    
    # Extract archived status
    archived = getattr(raw_obj, 'archived', False)
    if archived is None:
        archived = False
    
    return Task(
        id=obj_id,
        properties=TaskProperties(**standard),
        created_at=_to_iso_string(created_at),
        updated_at=_to_iso_string(updated_at),
        archived=archived
    )


def normalize_note(raw_obj: Any) -> Note:
    """Convert raw HubSpot note object to Klavis Note schema."""
    # Extract ID - handle both SDK objects and dicts
    obj_id = getattr(raw_obj, 'id', None)
    if obj_id is None and isinstance(raw_obj, dict):
        obj_id = raw_obj.get('id', '')
    obj_id = str(obj_id) if obj_id else ''
    
    # Extract and convert properties
    raw_props = getattr(raw_obj, 'properties', None)
    if raw_props is None and isinstance(raw_obj, dict):
        raw_props = raw_obj.get('properties', {})
    raw_props = _to_dict_safe(raw_props)
    
    known_fields = ['hs_note_body', 'hs_timestamp', 'hubspot_owner_id']
    
    standard, additional = extract_standard_properties(raw_props, known_fields)
    standard['additional_properties'] = additional
    
    # Extract timestamps
    created_at = getattr(raw_obj, 'created_at', None) or raw_props.get('createdate')
    updated_at = getattr(raw_obj, 'updated_at', None) or raw_props.get('lastmodifieddate')
    
    # Extract archived status
    archived = getattr(raw_obj, 'archived', False)
    if archived is None:
        archived = False
    
    return Note(
        id=obj_id,
        properties=NoteProperties(**standard),
        created_at=_to_iso_string(created_at),
        updated_at=_to_iso_string(updated_at),
        archived=archived
    )

