import logging
from typing import Any, Dict, List, Optional
from .base import get_salesforce_conn, handle_salesforce_error, format_success_response

# Configure logging
logger = logging.getLogger(__name__)

async def get_accounts(limit: int = 50, fields: Optional[List[str]] = None, name_contains: Optional[str] = None, industry: Optional[str] = None, account_type: Optional[str] = None) -> Dict[str, Any]:
    """Get accounts with flexible filtering options."""
    logger.info(f"Executing tool: get_accounts with limit: {limit}, name_contains: {name_contains}, industry: {industry}, account_type: {account_type}")
    try:
        sf = get_salesforce_conn()
        
        # Default fields if none specified
        if not fields:
            fields = ['Id', 'Name', 'Type', 'Industry', 'BillingStreet', 'BillingCity', 
                     'BillingState', 'BillingCountry', 'Phone', 'Website', 'OwnerId', 
                     'CreatedDate', 'LastModifiedDate']
        
        field_list = ', '.join(fields)
        
        # Build query with optional filters
        where_clauses = []
        if name_contains:
            # Case-insensitive search by trying multiple case variations
            name_variations = [
                name_contains.lower(),
                name_contains.upper(),
                name_contains.capitalize(),
                name_contains
            ]
            name_like_conditions = " OR ".join([f"Name LIKE '%{variation}%'" for variation in set(name_variations)])
            where_clauses.append(f"({name_like_conditions})")
            
        if industry:
            where_clauses.append(f"Industry = '{industry}'")
        if account_type:
            where_clauses.append(f"Type = '{account_type}'")
        
        where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        query = f"SELECT {field_list} FROM Account{where_clause} ORDER BY Name LIMIT {limit}"
        
        result = sf.query(query)
        return dict(result)
        
    except Exception as e:
        logger.exception(f"Error executing tool get_accounts: {e}")
        raise e

async def get_account_by_id(account_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get a specific account by ID."""
    logger.info(f"Executing tool: get_account_by_id with account_id: {account_id}")
    try:
        sf = get_salesforce_conn()
        
        # Default fields if none specified
        if not fields:
            fields = ['Id', 'Name', 'Type', 'Industry', 'Description', 'BillingStreet', 
                     'BillingCity', 'BillingState', 'BillingCountry', 'BillingPostalCode',
                     'ShippingStreet', 'ShippingCity', 'ShippingState', 'ShippingCountry', 
                     'ShippingPostalCode', 'Phone', 'Fax', 'Website', 'NumberOfEmployees',
                     'AnnualRevenue', 'OwnerId', 'CreatedDate', 'LastModifiedDate']
        
        field_list = ', '.join(fields)
        query = f"SELECT {field_list} FROM Account WHERE Id = '{account_id}'"
        
        result = sf.query(query)
        return dict(result)
        
    except Exception as e:
        logger.exception(f"Error executing tool get_account_by_id: {e}")
        raise e

async def create_account(account_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new account."""
    logger.info(f"Executing tool: create_account")
    try:
        sf = get_salesforce_conn()
        
        # Validate required fields
        if 'Name' not in account_data:
            return {
                "success": False,
                "error": "Name is required for Account creation",
                "message": "Failed to create Account"
            }
        
        result = sf.Account.create(account_data)
        
        if result.get('success'):
            return format_success_response(result.get('id'), "created", "Account", account_data)
        else:
            return {
                "success": False,
                "errors": result.get('errors', []),
                "message": "Failed to create Account"
            }
            
    except Exception as e:
        return handle_salesforce_error(e, "create", "Account")

async def update_account(account_id: str, account_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing account."""
    logger.info(f"Executing tool: update_account with account_id: {account_id}")
    try:
        sf = get_salesforce_conn()
        
        result = sf.Account.update(account_id, account_data)
        
        # simple-salesforce returns HTTP status code for updates
        if result == 204:  # HTTP 204 No Content indicates successful update
            return format_success_response(account_id, "updated", "Account", account_data)
        else:
            return {
                "success": False,
                "message": f"Failed to update Account. Status code: {result}"
            }
            
    except Exception as e:
        return handle_salesforce_error(e, "update", "Account")

async def delete_account(account_id: str) -> Dict[str, Any]:
    """Delete an account."""
    logger.info(f"Executing tool: delete_account with account_id: {account_id}")
    try:
        sf = get_salesforce_conn()
        
        result = sf.Account.delete(account_id)
        
        # simple-salesforce returns HTTP status code for deletes
        if result == 204:  # HTTP 204 No Content indicates successful deletion
            return format_success_response(account_id, "deleted", "Account")
        else:
            return {
                "success": False,
                "message": f"Failed to delete Account. Status code: {result}"
            }
            
    except Exception as e:
        return handle_salesforce_error(e, "delete", "Account") 