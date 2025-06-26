import logging
from typing import Any, Dict
from contextvars import ContextVar
from simple_salesforce import Salesforce
from simple_salesforce.exceptions import SalesforceError

# Configure logging
logger = logging.getLogger(__name__)

# Context variables to store the access token and instance URL for each request
access_token_context: ContextVar[str] = ContextVar('access_token')
instance_url_context: ContextVar[str] = ContextVar('instance_url')

def get_salesforce_connection(access_token: str, instance_url: str) -> Salesforce:
    """Create Salesforce connection with access token."""
    return Salesforce(instance_url=instance_url, session_id=access_token)

def get_salesforce_conn() -> Salesforce:
    """Get the Salesforce connection from context - created fresh each time."""
    try:
        access_token = access_token_context.get()
        instance_url = instance_url_context.get()
        
        if not access_token or not instance_url:
            raise RuntimeError("Salesforce access token and instance URL are required. Provide them via x-auth-token and x-instance-url headers.")
        
        return get_salesforce_connection(access_token, instance_url)
    except LookupError:
        raise RuntimeError("Salesforce credentials not found in request context")

def handle_salesforce_error(e: Exception, operation: str, object_type: str = "") -> Dict[str, Any]:
    """Handle Salesforce errors and return standardized error response."""
    if isinstance(e, SalesforceError):
        logger.error(f"Salesforce API error during {operation}: {e}")
        error_msg = str(e)
        # Try to extract more meaningful error information
        if hasattr(e, 'content') and e.content:
            try:
                error_content = e.content[0]['message'] if isinstance(e.content, list) else e.content
                if isinstance(error_content, dict) and 'message' in error_content:
                    error_msg = error_content['message']
            except:
                pass
        return {
            "success": False,
            "error": f"Salesforce API Error: {error_msg}",
            "message": f"Failed to {operation} {object_type}".strip()
        }
    else:
        logger.exception(f"Error during {operation}: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to {operation} {object_type}".strip()
        }

def format_success_response(record_id: str, operation: str, object_type: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Format a successful operation response."""
    response = {
        "success": True,
        "id": record_id,
        "message": f"{object_type} {operation} successfully",
        "object_type": object_type
    }
    if data:
        response["data"] = data
    return response

def create_case_insensitive_like_conditions(search_term: str, *field_names: str) -> str:
    """Create case-insensitive LIKE conditions for multiple fields."""
    if not search_term or not field_names:
        return ""
    
    variations = [
        search_term.lower(),
        search_term.upper(),
        search_term.capitalize(),
        search_term
    ]
    
    all_conditions = []
    for field_name in field_names:
        field_conditions = [f"{field_name} LIKE '%{variation}%'" for variation in set(variations)]
        all_conditions.extend(field_conditions)
    
    return " OR ".join(all_conditions) 