import logging
from typing import Any, Dict, List, Optional
from .base import get_salesforce_conn, handle_salesforce_error, format_success_response

# Configure logging
logger = logging.getLogger(__name__)

async def get_contacts(account_id: Optional[str] = None, limit: int = 50, fields: Optional[List[str]] = None, name_contains: Optional[str] = None, email_contains: Optional[str] = None, title_contains: Optional[str] = None) -> Dict[str, Any]:
    """Get contacts with flexible filtering options."""
    logger.info(f"Executing tool: get_contacts with account_id: {account_id}, limit: {limit}, name_contains: {name_contains}, email_contains: {email_contains}, title_contains: {title_contains}")
    try:
        sf = get_salesforce_conn()
        
        # Default fields if none specified
        if not fields:
            fields = ['Id', 'FirstName', 'LastName', 'Email', 'Phone', 'Title', 'Department',
                     'AccountId', 'Account.Name', 'OwnerId', 'CreatedDate', 'LastModifiedDate']
        
        field_list = ', '.join(fields)
        
        # Build query with optional filters
        where_clauses = []
        if account_id:
            where_clauses.append(f"AccountId = '{account_id}'")
        if name_contains:
            # Case-insensitive search for first or last name
            name_variations = [
                name_contains.lower(),
                name_contains.upper(),
                name_contains.capitalize(),
                name_contains
            ]
            name_like_conditions = []
            for variation in set(name_variations):
                name_like_conditions.extend([
                    f"FirstName LIKE '%{variation}%'",
                    f"LastName LIKE '%{variation}%'"
                ])
            where_clauses.append(f"({' OR '.join(name_like_conditions)})")
        if email_contains:
            # Case-insensitive email search
            email_variations = [
                email_contains.lower(),
                email_contains.upper(),
                email_contains
            ]
            email_like_conditions = " OR ".join([f"Email LIKE '%{variation}%'" for variation in set(email_variations)])
            where_clauses.append(f"({email_like_conditions})")
        if title_contains:
            # Case-insensitive title search
            title_variations = [
                title_contains.lower(),
                title_contains.upper(),
                title_contains.capitalize(),
                title_contains
            ]
            title_like_conditions = " OR ".join([f"Title LIKE '%{variation}%'" for variation in set(title_variations)])
            where_clauses.append(f"({title_like_conditions})")
        
        where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        query = f"SELECT {field_list} FROM Contact{where_clause} ORDER BY LastName, FirstName LIMIT {limit}"
        
        result = sf.query(query)
        return dict(result)
        
    except Exception as e:
        logger.exception(f"Error executing tool get_contacts: {e}")
        raise e

async def get_contact_by_id(contact_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get a specific contact by ID."""
    logger.info(f"Executing tool: get_contact_by_id with contact_id: {contact_id}")
    try:
        sf = get_salesforce_conn()
        
        # Default fields if none specified
        if not fields:
            fields = ['Id', 'FirstName', 'LastName', 'Email', 'Phone', 'MobilePhone', 
                     'Title', 'Department', 'AccountId', 'Account.Name', 'MailingStreet',
                     'MailingCity', 'MailingState', 'MailingCountry', 'MailingPostalCode',
                     'Birthdate', 'LeadSource', 'OwnerId', 'CreatedDate', 'LastModifiedDate']
        
        field_list = ', '.join(fields)
        query = f"SELECT {field_list} FROM Contact WHERE Id = '{contact_id}'"
        
        result = sf.query(query)
        return dict(result)
        
    except Exception as e:
        logger.exception(f"Error executing tool get_contact_by_id: {e}")
        raise e

async def create_contact(contact_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new contact."""
    logger.info(f"Executing tool: create_contact")
    try:
        sf = get_salesforce_conn()
        
        # Validate required fields
        if 'LastName' not in contact_data:
            return {
                "success": False,
                "error": "LastName is required for Contact creation",
                "message": "Failed to create Contact"
            }
        
        result = sf.Contact.create(contact_data)
        
        if result.get('success'):
            return format_success_response(result.get('id'), "created", "Contact", contact_data)
        else:
            return {
                "success": False,
                "errors": result.get('errors', []),
                "message": "Failed to create Contact"
            }
            
    except Exception as e:
        return handle_salesforce_error(e, "create", "Contact")

async def update_contact(contact_id: str, contact_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing contact."""
    logger.info(f"Executing tool: update_contact with contact_id: {contact_id}")
    try:
        sf = get_salesforce_conn()
        
        result = sf.Contact.update(contact_id, contact_data)
        
        # simple-salesforce returns HTTP status code for updates
        if result == 204:  # HTTP 204 No Content indicates successful update
            return format_success_response(contact_id, "updated", "Contact", contact_data)
        else:
            return {
                "success": False,
                "message": f"Failed to update Contact. Status code: {result}"
            }
            
    except Exception as e:
        return handle_salesforce_error(e, "update", "Contact")

async def delete_contact(contact_id: str) -> Dict[str, Any]:
    """Delete a contact."""
    logger.info(f"Executing tool: delete_contact with contact_id: {contact_id}")
    try:
        sf = get_salesforce_conn()
        
        result = sf.Contact.delete(contact_id)
        
        # simple-salesforce returns HTTP status code for deletes
        if result == 204:  # HTTP 204 No Content indicates successful deletion
            return format_success_response(contact_id, "deleted", "Contact")
        else:
            return {
                "success": False,
                "message": f"Failed to delete Contact. Status code: {result}"
            }
            
    except Exception as e:
        return handle_salesforce_error(e, "delete", "Contact") 