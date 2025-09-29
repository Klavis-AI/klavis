import logging
import json
from typing import Optional

from hubspot.crm.objects import (
    SimplePublicObjectInputForCreate,
    SimplePublicObjectInput,
)

from .base import get_hubspot_client


# Configure logging
logger = logging.getLogger(__name__)


async def hubspot_get_tasks(limit: int = 10):
    """
    Fetch a list of tasks from HubSpot.

    Parameters:
    - limit: Number of tasks to return

    Returns:
    - List of task records
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
        logger.info(f"Fetched {len(result.results)} tasks successfully.")
        return result
    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        return None


async def hubspot_get_task_by_id(task_id: str):
    """
    Fetch a task by its ID.

    Parameters:
    - task_id: HubSpot task ID

    Returns:
    - Task object
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
        print(f"---Result: {result}")
        logger.info(f"Fetched task ID: {task_id} successfully.")
        return result
    except Exception as e:
        logger.error(f"Error fetching task by ID: {e}")
        return None


async def hubspot_create_task(properties: str):
    """
    Create a new task.

    Parameters:
    - properties: JSON string of task properties (see HubSpot docs)

    Returns:
    - Newly created task
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
        logger.info("Task created successfully.")
        return result
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        return f"Error occurred: {e}"


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


