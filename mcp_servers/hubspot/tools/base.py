import logging
import os
from contextvars import ContextVar
from hubspot import HubSpot
from typing import Optional, Any, Dict
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Normalization Utilities (Klavis Interface Layer)
# ============================================================================

def get_path(data: Dict, path: str) -> Any:
    """Safe dot-notation access. Returns None if path fails."""
    if not data:
        return None
    current = data
    for key in path.split('.'):
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    return current


def normalize(source: Dict, mapping: Dict[str, Any]) -> Dict:
    """
    Creates a new clean dictionary based strictly on the mapping rules.
    Excludes fields with None/null values from the output.
    Args:
        source: Raw vendor JSON/dict.
        mapping: Dict of { "TargetFieldName": "Source.Path" OR Lambda_Function }
    """
    clean_data = {}
    for target_key, rule in mapping.items():
        value = None
        if isinstance(rule, str):
            value = get_path(source, rule)
        elif callable(rule):
            try:
                value = rule(source)
            except Exception:
                value = None
        if value is not None:
            clean_data[target_key] = value
    return clean_data


# ============================================================================
# Mapping Rules for HubSpot Objects (Klavis-defined schemas)
# ============================================================================

# Contact mapping rules
CONTACT_RULES = {
    "id": "id",
    "email": "email",
    "firstName": "firstname",
    "lastName": "lastname",
    "phone": "phone",
    "mobilePhone": "mobilephone",
    "company": "company",
    "jobTitle": "jobtitle",
    "website": "website",
    "address": "address",
    "city": "city",
    "state": "state",
    "postalCode": "zip",
    "country": "country",
    "lifecycleStage": "lifecyclestage",
    "leadStatus": "hs_lead_status",
    "ownerId": "hubspot_owner_id",
    "createdAt": "createdate",
    "updatedAt": "lastmodifieddate",
}

# Company mapping rules
COMPANY_RULES = {
    "id": "id",
    "name": "name",
    "domain": "domain",
    "website": "website",
    "phone": "phone",
    "address": "address",
    "city": "city",
    "state": "state",
    "postalCode": "zip",
    "country": "country",
    "industry": "industry",
    "employeeCount": "numberofemployees",
    "annualRevenue": "annualrevenue",
    "description": "description",
    "type": "type",
    "lifecycleStage": "lifecyclestage",
    "leadStatus": "hs_lead_status",
    "ownerId": "hubspot_owner_id",
    "createdAt": "createdate",
    "updatedAt": "hs_lastmodifieddate",
}

# Deal mapping rules
DEAL_RULES = {
    "id": "id",
    "name": "dealname",
    "amount": "amount",
    "stage": "dealstage",
    "stageLabel": "dealstage_label",
    "pipeline": "pipeline",
    "closeDate": "closedate",
    "dealType": "dealtype",
    "description": "description",
    "ownerId": "hubspot_owner_id",
    "createdAt": "createdate",
    "updatedAt": "hs_lastmodifieddate",
}

# Ticket mapping rules
TICKET_RULES = {
    "id": "id",
    "subject": "subject",
    "content": "content",
    "status": "hs_ticket_status",
    "priority": "hs_ticket_priority",
    "category": "hs_ticket_category",
    "pipeline": "hs_pipeline",
    "pipelineStage": "hs_pipeline_stage",
    "ownerId": "hubspot_owner_id",
    "createdAt": "createdate",
    "updatedAt": "hs_lastmodifieddate",
}

# Task mapping rules
TASK_RULES = {
    "id": "id",
    "subject": "hs_task_subject",
    "body": "hs_task_body",
    "status": "hs_task_status",
    "priority": "hs_task_priority",
    "type": "hs_task_type",
    "timestamp": "hs_timestamp",
    "ownerId": "hubspot_owner_id",
}

# Property mapping rules
PROPERTY_RULES = {
    "name": "name",
    "label": "label",
    "type": "type",
    "fieldType": "field_type",
}


def normalize_crm_object(obj: Any, rules: Dict[str, Any]) -> Dict:
    """
    Normalize a HubSpot CRM object (SimplePublicObject) to Klavis schema.
    Handles both raw dicts and HubSpot SDK objects.
    """
    if obj is None:
        return {}
    
    # Extract properties from SDK object or dict
    if hasattr(obj, 'properties'):
        props = dict(obj.properties) if obj.properties else {}
        obj_id = getattr(obj, 'id', None)
    elif isinstance(obj, dict):
        props = obj.get('properties', obj)
        obj_id = obj.get('id')
    else:
        return {}
    
    # Add id to props for normalization
    if obj_id:
        props['id'] = obj_id
    
    return normalize(props, rules)


def normalize_contact(obj: Any) -> Dict:
    """Normalize a contact object."""
    return normalize_crm_object(obj, CONTACT_RULES)


def normalize_company(obj: Any) -> Dict:
    """Normalize a company object."""
    return normalize_crm_object(obj, COMPANY_RULES)


def normalize_deal(obj: Any) -> Dict:
    """Normalize a deal object."""
    return normalize_crm_object(obj, DEAL_RULES)


def normalize_ticket(obj: Any) -> Dict:
    """Normalize a ticket object."""
    return normalize_crm_object(obj, TICKET_RULES)


def normalize_task(obj: Any) -> Dict:
    """Normalize a task object."""
    return normalize_crm_object(obj, TASK_RULES)


def normalize_property(prop: Any) -> Dict:
    """Normalize a property metadata object."""
    if prop is None:
        return {}
    
    if hasattr(prop, 'name'):
        # SDK object
        data = {
            'name': getattr(prop, 'name', None),
            'label': getattr(prop, 'label', None),
            'type': getattr(prop, 'type', None),
            'field_type': getattr(prop, 'field_type', None),
        }
    elif isinstance(prop, dict):
        data = prop
    else:
        return {}
    
    return normalize(data, PROPERTY_RULES)

load_dotenv()

# Context variable to store the access token for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

def get_auth_token() -> str:
    """Get the authentication token from context."""
    try:
        token = auth_token_context.get()
        if not token:
            # Fallback to environment variable if no token in context
            token = os.getenv("HUBSPOT_ACCESS_TOKEN")
            if not token:
                raise RuntimeError("No authentication token available")
        return token
    except LookupError:
        token = os.getenv("HUBSPOT_ACCESS_TOKEN")
        if not token:
            raise RuntimeError("Authentication token not found in request context or environment")
        return token

def get_hubspot_client() -> Optional[HubSpot]:
    """Get HubSpot client with auth token from context."""
    try:
        auth_token = get_auth_token()
        client = HubSpot(access_token=auth_token)
        return client
    except RuntimeError as e:
        logger.warning(f"Failed to get auth token: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize HubSpot client: {e}")
        return None
