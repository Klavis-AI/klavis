import logging
from typing import Any, Dict, List, Optional
from .base import get_salesforce_conn, handle_salesforce_error, format_success_response

# Configure logging
logger = logging.getLogger(__name__)

# Task-related functions
async def get_tasks(assigned_to: Optional[str] = None, status: Optional[str] = None, limit: int = 50, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get tasks, optionally filtered by assignee or status."""
    logger.info(f"Executing tool: get_tasks with assigned_to: {assigned_to}, status: {status}, limit: {limit}")
    try:
        sf = get_salesforce_conn()
        
        if not fields:
            fields = ['Id', 'Subject', 'Status', 'Priority', 'ActivityDate', 'WhoId', 'WhatId',
                     'Account.Name', 'Contact.Name', 'OwnerId', 'CreatedDate', 'LastModifiedDate']
        
        field_list = ', '.join(fields)
        where_clauses = []
        if assigned_to:
            where_clauses.append(f"OwnerId = '{assigned_to}'")
        if status:
            where_clauses.append(f"Status = '{status}'")
        
        where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        query = f"SELECT {field_list} FROM Task{where_clause} ORDER BY ActivityDate DESC LIMIT {limit}"
        
        result = sf.query(query)
        return dict(result)
    except Exception as e:
        logger.exception(f"Error executing tool get_tasks: {e}")
        raise e

async def get_task_by_id(task_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get a specific task by ID."""
    logger.info(f"Executing tool: get_task_by_id with task_id: {task_id}")
    try:
        sf = get_salesforce_conn()
        
        if not fields:
            fields = ['Id', 'Subject', 'Status', 'Priority', 'ActivityDate', 'Description',
                     'WhoId', 'WhatId', 'Account.Name', 'Contact.Name', 'OwnerId',
                     'CreatedDate', 'LastModifiedDate']
        
        field_list = ', '.join(fields)
        query = f"SELECT {field_list} FROM Task WHERE Id = '{task_id}'"
        
        result = sf.query(query)
        return dict(result)
    except Exception as e:
        logger.exception(f"Error executing tool get_task_by_id: {e}")
        raise e

async def create_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new task."""
    logger.info(f"Executing tool: create_task")
    try:
        sf = get_salesforce_conn()
        
        if 'Subject' not in task_data:
            return {
                "success": False,
                "error": "Subject is required for Task creation",
                "message": "Failed to create Task"
            }
        
        result = sf.Task.create(task_data)
        
        if result.get('success'):
            return format_success_response(result.get('id'), "created", "Task", task_data)
        else:
            return {
                "success": False,
                "errors": result.get('errors', []),
                "message": "Failed to create Task"
            }
    except Exception as e:
        return handle_salesforce_error(e, "create", "Task")

async def update_task(task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing task."""
    logger.info(f"Executing tool: update_task with task_id: {task_id}")
    try:
        sf = get_salesforce_conn()
        result = sf.Task.update(task_id, task_data)
        
        if result == 204:
            return format_success_response(task_id, "updated", "Task", task_data)
        else:
            return {"success": False, "message": f"Failed to update Task. Status code: {result}"}
    except Exception as e:
        return handle_salesforce_error(e, "update", "Task")

async def delete_task(task_id: str) -> Dict[str, Any]:
    """Delete a task."""
    logger.info(f"Executing tool: delete_task with task_id: {task_id}")
    try:
        sf = get_salesforce_conn()
        result = sf.Task.delete(task_id)
        
        if result == 204:
            return format_success_response(task_id, "deleted", "Task")
        else:
            return {"success": False, "message": f"Failed to delete Task. Status code: {result}"}
    except Exception as e:
        return handle_salesforce_error(e, "delete", "Task")

# Event-related functions
async def get_events(assigned_to: Optional[str] = None, limit: int = 50, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get events, optionally filtered by assignee."""
    logger.info(f"Executing tool: get_events with assigned_to: {assigned_to}, limit: {limit}")
    try:
        sf = get_salesforce_conn()
        
        if not fields:
            fields = ['Id', 'Subject', 'StartDateTime', 'EndDateTime', 'Location', 'WhoId', 'WhatId',
                     'Account.Name', 'Contact.Name', 'OwnerId', 'CreatedDate', 'LastModifiedDate']
        
        field_list = ', '.join(fields)
        where_clause = f" WHERE OwnerId = '{assigned_to}'" if assigned_to else ""
        query = f"SELECT {field_list} FROM Event{where_clause} ORDER BY StartDateTime DESC LIMIT {limit}"
        
        result = sf.query(query)
        return dict(result)
    except Exception as e:
        logger.exception(f"Error executing tool get_events: {e}")
        raise e

async def get_event_by_id(event_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get a specific event by ID."""
    logger.info(f"Executing tool: get_event_by_id with event_id: {event_id}")
    try:
        sf = get_salesforce_conn()
        
        if not fields:
            fields = ['Id', 'Subject', 'StartDateTime', 'EndDateTime', 'Location', 'Description',
                     'WhoId', 'WhatId', 'Account.Name', 'Contact.Name', 'OwnerId',
                     'CreatedDate', 'LastModifiedDate']
        
        field_list = ', '.join(fields)
        query = f"SELECT {field_list} FROM Event WHERE Id = '{event_id}'"
        
        result = sf.query(query)
        return dict(result)
    except Exception as e:
        logger.exception(f"Error executing tool get_event_by_id: {e}")
        raise e

async def create_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new event."""
    logger.info(f"Executing tool: create_event")
    try:
        sf = get_salesforce_conn()
        
        required_fields = ['Subject', 'StartDateTime', 'EndDateTime']
        missing_fields = [field for field in required_fields if field not in event_data]
        
        if missing_fields:
            return {
                "success": False,
                "error": f"Required fields missing: {', '.join(missing_fields)}",
                "message": "Failed to create Event"
            }
        
        result = sf.Event.create(event_data)
        
        if result.get('success'):
            return format_success_response(result.get('id'), "created", "Event", event_data)
        else:
            return {
                "success": False,
                "errors": result.get('errors', []),
                "message": "Failed to create Event"
            }
    except Exception as e:
        return handle_salesforce_error(e, "create", "Event")

async def update_event(event_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing event."""
    logger.info(f"Executing tool: update_event with event_id: {event_id}")
    try:
        sf = get_salesforce_conn()
        result = sf.Event.update(event_id, event_data)
        
        if result == 204:
            return format_success_response(event_id, "updated", "Event", event_data)
        else:
            return {"success": False, "message": f"Failed to update Event. Status code: {result}"}
    except Exception as e:
        return handle_salesforce_error(e, "update", "Event")

async def delete_event(event_id: str) -> Dict[str, Any]:
    """Delete an event."""
    logger.info(f"Executing tool: delete_event with event_id: {event_id}")
    try:
        sf = get_salesforce_conn()
        result = sf.Event.delete(event_id)
        
        if result == 204:
            return format_success_response(event_id, "deleted", "Event")
        else:
            return {"success": False, "message": f"Failed to delete Event. Status code: {result}"}
    except Exception as e:
        return handle_salesforce_error(e, "delete", "Event") 