"""
HubSpot Tasks API tools with Klavis sanitization layer.

All responses are validated through Pydantic schemas.
All errors are sanitized to expose only HTTP status codes.
"""

import logging
import json
from hubspot.crm.objects import (
    SimplePublicObjectInputForCreate,
    SimplePublicObjectInput,
)

from .base import get_hubspot_client, safe_api_call
from .schemas import (
    Task,
    TaskList,
    TaskProperties,
    CreateResult,
    UpdateResult,
    DeleteResult,
    normalize_task
)
from .errors import (
    KlavisError,
    ValidationError,
    sanitize_exception
)

# Configure logging
logger = logging.getLogger(__name__)

# Common task properties to request
TASK_PROPERTIES = [
    "hs_task_subject",
    "hs_task_body",
    "hs_task_status",
    "hs_task_priority",
    "hs_timestamp",
    "hubspot_owner_id",
]


async def hubspot_get_tasks(limit: int = 10) -> TaskList:
    """
    Fetch a list of tasks from HubSpot.

    Parameters:
    - limit: Number of tasks to return

    Returns:
    - Klavis-normalized TaskList schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Fetching up to {limit} tasks...")
        
        result = safe_api_call(
            client.crm.objects.tasks.basic_api.get_page,
            resource_type="task",
            limit=limit,
            properties=TASK_PROPERTIES
        )
        
        # Normalize response through Klavis schema
        tasks = []
        for raw_task in getattr(result, 'results', []) or []:
            tasks.append(normalize_task(raw_task))
        
        logger.info(f"Fetched {len(tasks)} tasks successfully.")
        return TaskList(
            tasks=tasks,
            total=len(tasks),
            has_more=bool(getattr(result, 'paging', None))
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="task")


async def hubspot_get_task_by_id(task_id: str) -> Task:
    """
    Fetch a task by its ID.

    Parameters:
    - task_id: HubSpot task ID

    Returns:
    - Klavis-normalized Task schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Fetching task ID: {task_id}...")
        
        result = safe_api_call(
            client.crm.objects.tasks.basic_api.get_by_id,
            resource_type="task",
            resource_id=task_id,
            task_id=task_id,
            properties=TASK_PROPERTIES
        )
        
        logger.info(f"Fetched task ID: {task_id} successfully.")
        return normalize_task(result)
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="task", resource_id=task_id)


async def hubspot_create_task(properties: str) -> CreateResult:
    """
    Create a new task.

    Parameters:
    - properties: JSON string of task properties

    Returns:
    - Klavis-normalized CreateResult schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info("Creating new task...")
        
        # Parse and validate input
        try:
            props = json.loads(properties)
        except json.JSONDecodeError:
            raise ValidationError(resource_type="task")
        
        data = SimplePublicObjectInputForCreate(properties=props)
        result = safe_api_call(
            client.crm.objects.tasks.basic_api.create,
            resource_type="task",
            simple_public_object_input_for_create=data
        )
        
        logger.info("Task created successfully.")
        return CreateResult(
            status="success",
            message="Task created successfully",
            resource_id=getattr(result, 'id', None)
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="task")


async def hubspot_update_task_by_id(task_id: str, updates: str) -> UpdateResult:
    """
    Update a task by ID.

    Parameters:
    - task_id: HubSpot task ID
    - updates: JSON string of updated fields

    Returns:
    - Klavis-normalized UpdateResult schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Updating task ID: {task_id}...")
        
        # Parse and validate input
        try:
            updates_dict = json.loads(updates)
        except json.JSONDecodeError:
            raise ValidationError(resource_type="task")
        
        data = SimplePublicObjectInput(properties=updates_dict)
        safe_api_call(
            client.crm.objects.tasks.basic_api.update,
            resource_type="task",
            resource_id=task_id,
            task_id=task_id,
            simple_public_object_input=data
        )
        
        logger.info(f"Task ID: {task_id} updated successfully.")
        return UpdateResult(
            status="success",
            message="Task updated successfully",
            resource_id=task_id
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="task", resource_id=task_id)


async def hubspot_delete_task_by_id(task_id: str) -> DeleteResult:
    """
    Delete a task by ID.

    Parameters:
    - task_id: HubSpot task ID

    Returns:
    - Klavis-normalized DeleteResult schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Deleting task ID: {task_id}...")
        
        safe_api_call(
            client.crm.objects.tasks.basic_api.archive,
            resource_type="task",
            resource_id=task_id,
            task_id=task_id
        )
        
        logger.info(f"Task ID: {task_id} deleted successfully.")
        return DeleteResult(
            status="success",
            message="Task deleted successfully",
            resource_id=task_id
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="task", resource_id=task_id)
