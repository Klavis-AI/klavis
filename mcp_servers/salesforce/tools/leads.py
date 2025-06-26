import logging
from typing import Any, Dict, List, Optional
from .base import get_salesforce_conn, handle_salesforce_error, format_success_response

# Configure logging
logger = logging.getLogger(__name__)

async def get_leads(status: Optional[str] = None, limit: int = 50, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get leads, optionally filtered by status."""
    logger.info(f"Executing tool: get_leads with status: {status}, limit: {limit}")
    try:
        sf = get_salesforce_conn()
        
        # Default fields if none specified
        if not fields:
            fields = ['Id', 'FirstName', 'LastName', 'Email', 'Phone', 'Company', 'Title',
                     'Status', 'LeadSource', 'Industry', 'Rating', 'OwnerId', 
                     'CreatedDate', 'LastModifiedDate']
        
        field_list = ', '.join(fields)
        
        if status:
            query = f"SELECT {field_list} FROM Lead WHERE Status = '{status}' ORDER BY CreatedDate DESC LIMIT {limit}"
        else:
            query = f"SELECT {field_list} FROM Lead ORDER BY CreatedDate DESC LIMIT {limit}"
        
        result = sf.query(query)
        return dict(result)
        
    except Exception as e:
        logger.exception(f"Error executing tool get_leads: {e}")
        raise e

async def get_lead_by_id(lead_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get a specific lead by ID."""
    logger.info(f"Executing tool: get_lead_by_id with lead_id: {lead_id}")
    try:
        sf = get_salesforce_conn()
        
        # Default fields if none specified
        if not fields:
            fields = ['Id', 'FirstName', 'LastName', 'Email', 'Phone', 'MobilePhone',
                     'Company', 'Title', 'Status', 'LeadSource', 'Industry', 'Rating',
                     'Street', 'City', 'State', 'Country', 'PostalCode', 'Website',
                     'Description', 'NumberOfEmployees', 'AnnualRevenue', 'OwnerId',
                     'CreatedDate', 'LastModifiedDate']
        
        field_list = ', '.join(fields)
        query = f"SELECT {field_list} FROM Lead WHERE Id = '{lead_id}'"
        
        result = sf.query(query)
        return dict(result)
        
    except Exception as e:
        logger.exception(f"Error executing tool get_lead_by_id: {e}")
        raise e

async def create_lead(lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new lead."""
    logger.info(f"Executing tool: create_lead")
    try:
        sf = get_salesforce_conn()
        
        # Validate required fields
        required_fields = ['LastName', 'Company']
        missing_fields = [field for field in required_fields if field not in lead_data]
        
        if missing_fields:
            return {
                "success": False,
                "error": f"Required fields missing: {', '.join(missing_fields)}",
                "message": "Failed to create Lead"
            }
        
        result = sf.Lead.create(lead_data)
        
        if result.get('success'):
            return format_success_response(result.get('id'), "created", "Lead", lead_data)
        else:
            return {
                "success": False,
                "errors": result.get('errors', []),
                "message": "Failed to create Lead"
            }
            
    except Exception as e:
        return handle_salesforce_error(e, "create", "Lead")

async def update_lead(lead_id: str, lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing lead."""
    logger.info(f"Executing tool: update_lead with lead_id: {lead_id}")
    try:
        sf = get_salesforce_conn()
        
        result = sf.Lead.update(lead_id, lead_data)
        
        # simple-salesforce returns HTTP status code for updates
        if result == 204:  # HTTP 204 No Content indicates successful update
            return format_success_response(lead_id, "updated", "Lead", lead_data)
        else:
            return {
                "success": False,
                "message": f"Failed to update Lead. Status code: {result}"
            }
            
    except Exception as e:
        return handle_salesforce_error(e, "update", "Lead")

async def delete_lead(lead_id: str) -> Dict[str, Any]:
    """Delete a lead."""
    logger.info(f"Executing tool: delete_lead with lead_id: {lead_id}")
    try:
        sf = get_salesforce_conn()
        
        result = sf.Lead.delete(lead_id)
        
        # simple-salesforce returns HTTP status code for deletes
        if result == 204:  # HTTP 204 No Content indicates successful deletion
            return format_success_response(lead_id, "deleted", "Lead")
        else:
            return {
                "success": False,
                "message": f"Failed to delete Lead. Status code: {result}"
            }
            
    except Exception as e:
        return handle_salesforce_error(e, "delete", "Lead")

async def convert_lead(lead_id: str, conversion_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Convert a lead to account, contact, and optionally opportunity."""
    logger.info(f"Executing tool: convert_lead with lead_id: {lead_id}")
    try:
        sf = get_salesforce_conn()
        
        # Default conversion data if none provided
        if not conversion_data:
            conversion_data = {
                'doNotCreateOpportunity': True,  # Set to False to create opportunity
                'sendNotificationEmail': False
            }
        
        # Lead conversion is done via REST API
        conversion_url = f"sobjects/Lead/{lead_id}/convert"
        result = sf.restful(conversion_url, method='POST', json=conversion_data)
        
        if result.get('success'):
            return {
                "success": True,
                "message": "Lead converted successfully",
                "conversion_details": {
                    "lead_id": lead_id,
                    "account_id": result.get('accountId'),
                    "contact_id": result.get('contactId'),
                    "opportunity_id": result.get('opportunityId')
                }
            }
        else:
            return {
                "success": False,
                "errors": result.get('errors', []),
                "message": "Failed to convert Lead"
            }
            
    except Exception as e:
        return handle_salesforce_error(e, "convert", "Lead") 