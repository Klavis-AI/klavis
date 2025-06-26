import logging
from typing import Any, Dict, List, Optional
from .base import get_salesforce_conn, handle_salesforce_error, format_success_response

# Configure logging
logger = logging.getLogger(__name__)

async def get_campaigns(status: Optional[str] = None, type_filter: Optional[str] = None, limit: int = 50, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get campaigns, optionally filtered by status or type."""
    logger.info(f"Executing tool: get_campaigns with status: {status}, type: {type_filter}, limit: {limit}")
    try:
        sf = get_salesforce_conn()
        
        # Default fields if none specified
        if not fields:
            fields = ['Id', 'Name', 'Type', 'Status', 'StartDate', 'EndDate', 'IsActive',
                     'Description', 'BudgetedCost', 'ActualCost', 'ExpectedRevenue',
                     'NumberOfLeads', 'NumberOfConvertedLeads', 'NumberOfContacts',
                     'NumberOfOpportunities', 'NumberOfWonOpportunities', 'OwnerId',
                     'CreatedDate', 'LastModifiedDate']
        
        field_list = ', '.join(fields)
        
        # Build query with optional filters
        where_clauses = []
        if status:
            where_clauses.append(f"Status = '{status}'")
        if type_filter:
            where_clauses.append(f"Type = '{type_filter}'")
        
        where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        query = f"SELECT {field_list} FROM Campaign{where_clause} ORDER BY StartDate DESC LIMIT {limit}"
        
        result = sf.query(query)
        return dict(result)
        
    except Exception as e:
        logger.exception(f"Error executing tool get_campaigns: {e}")
        raise e

async def get_campaign_by_id(campaign_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get a specific campaign by ID."""
    logger.info(f"Executing tool: get_campaign_by_id with campaign_id: {campaign_id}")
    try:
        sf = get_salesforce_conn()
        
        # Default fields if none specified
        if not fields:
            fields = ['Id', 'Name', 'Type', 'Status', 'StartDate', 'EndDate', 'IsActive',
                     'Description', 'BudgetedCost', 'ActualCost', 'ExpectedRevenue',
                     'ExpectedResponse', 'NumberSent', 'NumberOfLeads', 'NumberOfConvertedLeads',
                     'NumberOfContacts', 'NumberOfResponses', 'NumberOfOpportunities',
                     'NumberOfWonOpportunities', 'AmountAllOpportunities', 'AmountWonOpportunities',
                     'OwnerId', 'CreatedDate', 'LastModifiedDate']
        
        field_list = ', '.join(fields)
        query = f"SELECT {field_list} FROM Campaign WHERE Id = '{campaign_id}'"
        
        result = sf.query(query)
        return dict(result)
        
    except Exception as e:
        logger.exception(f"Error executing tool get_campaign_by_id: {e}")
        raise e

async def create_campaign(campaign_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new campaign."""
    logger.info(f"Executing tool: create_campaign")
    try:
        sf = get_salesforce_conn()
        
        # Validate required fields
        if 'Name' not in campaign_data:
            return {
                "success": False,
                "error": "Name is required for Campaign creation",
                "message": "Failed to create Campaign"
            }
        
        result = sf.Campaign.create(campaign_data)
        
        if result.get('success'):
            return format_success_response(result.get('id'), "created", "Campaign", campaign_data)
        else:
            return {
                "success": False,
                "errors": result.get('errors', []),
                "message": "Failed to create Campaign"
            }
            
    except Exception as e:
        return handle_salesforce_error(e, "create", "Campaign")

async def update_campaign(campaign_id: str, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing campaign."""
    logger.info(f"Executing tool: update_campaign with campaign_id: {campaign_id}")
    try:
        sf = get_salesforce_conn()
        
        result = sf.Campaign.update(campaign_id, campaign_data)
        
        # simple-salesforce returns HTTP status code for updates
        if result == 204:  # HTTP 204 No Content indicates successful update
            return format_success_response(campaign_id, "updated", "Campaign", campaign_data)
        else:
            return {
                "success": False,
                "message": f"Failed to update Campaign. Status code: {result}"
            }
            
    except Exception as e:
        return handle_salesforce_error(e, "update", "Campaign")

async def delete_campaign(campaign_id: str) -> Dict[str, Any]:
    """Delete a campaign."""
    logger.info(f"Executing tool: delete_campaign with campaign_id: {campaign_id}")
    try:
        sf = get_salesforce_conn()
        
        result = sf.Campaign.delete(campaign_id)
        
        # simple-salesforce returns HTTP status code for deletes
        if result == 204:  # HTTP 204 No Content indicates successful deletion
            return format_success_response(campaign_id, "deleted", "Campaign")
        else:
            return {
                "success": False,
                "message": f"Failed to delete Campaign. Status code: {result}"
            }
            
    except Exception as e:
        return handle_salesforce_error(e, "delete", "Campaign") 