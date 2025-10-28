import logging
from typing import Any, Dict, List, Optional
from .base import get_salesforce_conn, handle_salesforce_error, format_success_response

# Configure logging
logger = logging.getLogger(__name__)

async def get_cases(account_id: Optional[str] = None, status: Optional[str] = None, priority: Optional[str] = None, limit: int = 50, fields: Optional[List[str]] = None, subject_contains: Optional[str] = None, case_type: Optional[str] = None) -> Dict[str, Any]:
    """Get cases with flexible filtering options."""
    logger.info(f"Executing tool: get_cases with account_id: {account_id}, status: {status}, priority: {priority}, limit: {limit}, subject_contains: {subject_contains}, case_type: {case_type}")
    try:
        sf = get_salesforce_conn()
        
        # Default fields if none specified
        if not fields:
            fields = ['Id', 'CaseNumber', 'Subject', 'Status', 'Priority', 'Type', 'Reason',
                     'AccountId', 'Account.Name', 'ContactId', 'Contact.Name', 'OwnerId',
                     'CreatedDate', 'LastModifiedDate', 'ClosedDate']
        
        field_list = ', '.join(fields)
        
        # Build query with optional filters
        where_clauses = []
        if account_id:
            where_clauses.append(f"AccountId = '{account_id}'")
        if status:
            where_clauses.append(f"Status = '{status}'")
        if priority:
            where_clauses.append(f"Priority = '{priority}'")
        if subject_contains:
            # Case-insensitive subject search
            subject_variations = [
                subject_contains.lower(),
                subject_contains.upper(),
                subject_contains.capitalize(),
                subject_contains
            ]
            subject_like_conditions = " OR ".join([f"Subject LIKE '%{variation}%'" for variation in set(subject_variations)])
            where_clauses.append(f"({subject_like_conditions})")
        if case_type:
            where_clauses.append(f"Type = '{case_type}'")
        
        where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        query = f"SELECT {field_list} FROM Case{where_clause} ORDER BY CreatedDate DESC LIMIT {limit}"
        
        result = sf.query(query)
        return dict(result)
        
    except Exception as e:
        logger.exception(f"Error executing tool get_cases: {e}")
        raise e

async def get_case_by_id(case_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get a specific case by ID."""
    logger.info(f"Executing tool: get_case_by_id with case_id: {case_id}")
    try:
        sf = get_salesforce_conn()
        
        # Default fields if none specified
        if not fields:
            fields = ['Id', 'CaseNumber', 'Subject', 'Description', 'Status', 'Priority', 
                     'Type', 'Reason', 'Origin', 'AccountId', 'Account.Name', 'ContactId',
                     'Contact.Name', 'Contact.Email', 'Contact.Phone', 'SuppliedName',
                     'SuppliedEmail', 'SuppliedPhone', 'SuppliedCompany', 'OwnerId',
                     'CreatedDate', 'LastModifiedDate', 'ClosedDate']
        
        field_list = ', '.join(fields)
        query = f"SELECT {field_list} FROM Case WHERE Id = '{case_id}'"
        
        result = sf.query(query)
        return dict(result)
        
    except Exception as e:
        logger.exception(f"Error executing tool get_case_by_id: {e}")
        raise e

async def create_case(case_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new case."""
    logger.info(f"Executing tool: create_case")
    try:
        sf = get_salesforce_conn()
        
        # Validate required fields (Subject is typically required)
        if 'Subject' not in case_data:
            return {
                "success": False,
                "error": "Subject is required for Case creation",
                "message": "Failed to create Case"
            }
        
        result = sf.Case.create(case_data)
        
        if result.get('success'):
            return format_success_response(result.get('id'), "created", "Case", case_data)
        else:
            return {
                "success": False,
                "errors": result.get('errors', []),
                "message": "Failed to create Case"
            }
            
    except Exception as e:
        return handle_salesforce_error(e, "create", "Case")

async def update_case(case_id: str, case_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing case."""
    logger.info(f"Executing tool: update_case with case_id: {case_id}")
    try:
        sf = get_salesforce_conn()
        
        result = sf.Case.update(case_id, case_data)
        
        # simple-salesforce returns HTTP status code for updates
        if result == 204:  # HTTP 204 No Content indicates successful update
            return format_success_response(case_id, "updated", "Case", case_data)
        else:
            return {
                "success": False,
                "message": f"Failed to update Case. Status code: {result}"
            }
            
    except Exception as e:
        return handle_salesforce_error(e, "update", "Case")

async def delete_case(case_id: str) -> Dict[str, Any]:
    """Delete a case."""
    logger.info(f"Executing tool: delete_case with case_id: {case_id}")
    try:
        sf = get_salesforce_conn()
        
        result = sf.Case.delete(case_id)
        
        # simple-salesforce returns HTTP status code for deletes
        if result == 204:  # HTTP 204 No Content indicates successful deletion
            return format_success_response(case_id, "deleted", "Case")
        else:
            return {
                "success": False,
                "message": f"Failed to delete Case. Status code: {result}"
            }
            
    except Exception as e:
        return handle_salesforce_error(e, "delete", "Case") 