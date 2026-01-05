import logging
import json
from typing import Optional, Dict, Any

from hubspot.crm.objects import (
    SimplePublicObjectInputForCreate,
    SimplePublicObjectInput,
)

from .base import get_hubspot_client, normalize_task


# Configure logging
logger = logging.getLogger(__name__)


async def hubspot_get_tasks(limit: int = 10) -> Dict[str, Any]:
    """
    Fetch a list of tasks from HubSpot.

    Parameters:
    - limit: Number of tasks to return

    Returns:
    - Normalized list of task records
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")

    try:
        logger.info(f"Fetching up to {limit} tasks...")
        common_properties = [
            "hs_task_subject",
            "hs_task_body",
            "hs_task_status",
            "hs_task_priority",
            "hs_timestamp",
            "hubspot_owner_id",
        ]
        result = client.crm.objects.tasks.basic_api.get_page(
            limit=limit,
            properties=common_properties,
        )
        
        # Normalize response
        tasks = [normalize_task(obj) for obj in (result.results or [])]
        
        logger.info(f"Fetched {len(tasks)} tasks successfully.")
        return {
            "count": len(tasks),
            "tasks": tasks,
            "hasMore": result.paging.next.after is not None if result.paging and result.paging.next else False,
        }
    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        raise e


async def hubspot_get_task_by_id(task_id: str) -> Dict[str, Any]:
    """
    Fetch a task by its ID.

    Parameters:
    - task_id: HubSpot task ID

    Returns:
    - Normalized task object
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")

    try:
        logger.info(f"Fetching task ID: {task_id}...")
        common_properties = [
            "hs_task_subject",
            "hs_task_body",
            "hs_task_status",
            "hs_task_priority",
            "hs_timestamp",
            "hubspot_owner_id",
        ]
        result = client.crm.objects.tasks.basic_api.get_by_id(
            task_id,
            properties=common_properties,
        )
        
        # Normalize response
        task = normalize_task(result)
        
        logger.info(f"Fetched task ID: {task_id} successfully.")
        return {"task": task}
    except Exception as e:
        logger.error(f"Error fetching task by ID: {e}")
        raise e


async def hubspot_create_task(properties: str) -> Dict[str, Any]:
    """
    Create a new task.

    Parameters:
    - properties: JSON string of task properties (see HubSpot docs)

    Returns:
    - Normalized newly created task
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")

    try:
        logger.info("Creating new task...")
        props = json.loads(properties)
        data = SimplePublicObjectInputForCreate(properties=props)
        result = client.crm.objects.tasks.basic_api.create(
            simple_public_object_input_for_create=data
        )
        
        # Normalize response
        task = normalize_task(result)
        
        logger.info("Task created successfully.")
        return {"task": task, "status": "created"}
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise e


async def hubspot_update_task_by_id(task_id: str, updates: str):
    """
    Update a task by ID.

    Parameters:
    - task_id: HubSpot task ID
    - updates: JSON string of updated fields

    Returns:
    - "Done" on success, error message otherwise
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")

    try:
        logger.info(f"Updating task ID: {task_id}...")
        data = SimplePublicObjectInput(properties=json.loads(updates))
        client.crm.objects.tasks.basic_api.update(task_id, data)
        logger.info(f"Task ID: {task_id} updated successfully.")
        return "Done"
    except Exception as e:
        logger.error(f"Update failed for task ID {task_id}: {e}")
        return f"Error occurred: {e}"


async def hubspot_delete_task_by_id(task_id: str):
    """
    Delete a task by ID.

    Parameters:
    - task_id: HubSpot task ID

    Returns:
    - "Deleted" on success, error message otherwise
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")

    try:
        logger.info(f"Deleting task ID: {task_id}...")
        client.crm.objects.tasks.basic_api.archive(task_id)
        logger.info(f"Task ID: {task_id} deleted successfully.")
        return "Deleted"
    except Exception as e:
        logger.error(f"Error deleting task ID {task_id}: {e}")
        return f"Error occurred: {e}"


