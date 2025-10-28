import logging
from typing import Any, Dict, List, Optional
from .base import get_salesforce_conn, handle_salesforce_error, format_success_response

# Configure logging
logger = logging.getLogger(__name__)

async def get_opportunities(
    account_id: Optional[str] = None, 
    stage: Optional[str] = None, 
    name_contains: Optional[str] = None,
    account_name_contains: Optional[str] = None,
    limit: int = 50, 
    fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Get opportunities, optionally filtered by account, stage, name, or account name."""
    logger.info(f"Executing tool: get_opportunities with account_id: {account_id}, stage: {stage}, name_contains: {name_contains}, account_name_contains: {account_name_contains}, limit: {limit}")
    try:
        sf = get_salesforce_conn()
        
        # Default fields if none specified
        if not fields:
            fields = ['Id', 'Name', 'StageName', 'Amount', 'CloseDate', 'Probability',
                     'AccountId', 'Account.Name', 'Type', 'LeadSource', 'OwnerId', 
                     'CreatedDate', 'LastModifiedDate']
        
        field_list = ', '.join(fields)
        
        # Build query with optional filters
        where_clauses = []
        if account_id:
            where_clauses.append(f"AccountId = '{account_id}'")
        if stage:
            where_clauses.append(f"StageName = '{stage}'")
        if name_contains:
            # Case-insensitive search by trying multiple case variations
            name_variations = [
                name_contains.lower(),
                name_contains.upper(), 
                name_contains.capitalize(),
                name_contains
            ]
            # Create OR conditions for different case variations
            name_like_conditions = " OR ".join([f"Name LIKE '%{variation}%'" for variation in set(name_variations)])
            where_clauses.append(f"({name_like_conditions})")
            
        if account_name_contains:
            # Case-insensitive search by trying multiple case variations
            account_variations = [
                account_name_contains.lower(),
                account_name_contains.upper(),
                account_name_contains.capitalize(), 
                account_name_contains
            ]
            # Create OR conditions for different case variations
            account_like_conditions = " OR ".join([f"Account.Name LIKE '%{variation}%'" for variation in set(account_variations)])
            where_clauses.append(f"({account_like_conditions})")
        
        where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        query = f"SELECT {field_list} FROM Opportunity{where_clause} ORDER BY CloseDate ASC LIMIT {limit}"
        
        result = sf.query(query)
        return dict(result)
        
    except Exception as e:
        logger.exception(f"Error executing tool get_opportunities: {e}")
        raise e

async def get_opportunity_by_id(opportunity_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get a specific opportunity by ID."""
    logger.info(f"Executing tool: get_opportunity_by_id with opportunity_id: {opportunity_id}")
    try:
        sf = get_salesforce_conn()
        
        # Default fields if none specified
        if not fields:
            fields = ['Id', 'Name', 'StageName', 'Amount', 'CloseDate', 'Probability',
                     'AccountId', 'Account.Name', 'Type', 'LeadSource', 'Description',
                     'NextStep', 'CompetitorName__c', 'DeliveryInstallationStatus__c',
                     'TrackingNumber__c', 'OrderNumber__c', 'CurrentGenerators__c',
                     'MainCompetitors__c', 'OwnerId', 'CreatedDate', 'LastModifiedDate']
        
        field_list = ', '.join(fields)
        query = f"SELECT {field_list} FROM Opportunity WHERE Id = '{opportunity_id}'"
        
        result = sf.query(query)
        return dict(result)
        
    except Exception as e:
        logger.exception(f"Error executing tool get_opportunity_by_id: {e}")
        raise e

async def create_opportunity(opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new opportunity."""
    logger.info(f"Executing tool: create_opportunity")
    try:
        sf = get_salesforce_conn()
        
        # Validate required fields
        required_fields = ['Name', 'StageName', 'CloseDate']
        missing_fields = [field for field in required_fields if field not in opportunity_data]
        
        if missing_fields:
            return {
                "success": False,
                "error": f"Required fields missing: {', '.join(missing_fields)}",
                "message": "Failed to create Opportunity"
            }
        
        result = sf.Opportunity.create(opportunity_data)
        
        if result.get('success'):
            return format_success_response(result.get('id'), "created", "Opportunity", opportunity_data)
        else:
            return {
                "success": False,
                "errors": result.get('errors', []),
                "message": "Failed to create Opportunity"
            }
            
    except Exception as e:
        return handle_salesforce_error(e, "create", "Opportunity")

async def update_opportunity(
    opportunity_id: str,
    closed_date: Optional[str] = None,
    stage: Optional[str] = None,
    amount: Optional[float] = None,
    next_step: Optional[str] = None,
    description: Optional[str] = None,
    owner_id: Optional[str] = None,
    account_id: Optional[str] = None
) -> Dict[str, Any]:
    """Update an existing opportunity."""
    logger.info(f"Executing tool: update_opportunity with opportunity_id: {opportunity_id}")
    try:
        sf = get_salesforce_conn()
        
        # Build update data from provided parameters
        opportunity_data = {}
        if closed_date is not None:
            opportunity_data['CloseDate'] = closed_date
        if stage is not None:
            opportunity_data['StageName'] = stage
        if amount is not None:
            opportunity_data['Amount'] = amount
        if next_step is not None:
            opportunity_data['NextStep'] = next_step
        if description is not None:
            opportunity_data['Description'] = description
        if owner_id is not None:
            opportunity_data['OwnerId'] = owner_id
        if account_id is not None:
            opportunity_data['AccountId'] = account_id
        
        # Only update if there's data to update
        if not opportunity_data:
            return {
                "success": False,
                "message": "No fields provided to update"
            }
        
        result = sf.Opportunity.update(opportunity_id, opportunity_data)
        
        # simple-salesforce returns HTTP status code for updates
        if result == 204:  # HTTP 204 No Content indicates successful update
            return format_success_response(opportunity_id, "updated", "Opportunity", opportunity_data)
        else:
            return {
                "success": False,
                "message": f"Failed to update Opportunity. Status code: {result}"
            }
            
    except Exception as e:
        return handle_salesforce_error(e, "update", "Opportunity")

async def delete_opportunity(opportunity_id: str) -> Dict[str, Any]:
    """Delete an opportunity."""
    logger.info(f"Executing tool: delete_opportunity with opportunity_id: {opportunity_id}")
    try:
        sf = get_salesforce_conn()
        
        result = sf.Opportunity.delete(opportunity_id)
        
        # simple-salesforce returns HTTP status code for deletes
        if result == 204:  # HTTP 204 No Content indicates successful deletion
            return format_success_response(opportunity_id, "deleted", "Opportunity")
        else:
            return {
                "success": False,
                "message": f"Failed to delete Opportunity. Status code: {result}"
            }
            
    except Exception as e:
        return handle_salesforce_error(e, "delete", "Opportunity") 