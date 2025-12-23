import httpx
from .base import get_apollo_client

async def apollo_create_tasks(
    user_id: str,
    contact_ids: list,
    priority: str,
    due_at: str,
    task_type: str,
    status: str,
    note: str = None
) -> dict:
    """
    Create tasks for multiple contacts in Apollo to track upcoming actions.

    Parameters:
    - user_id (str): Required. ID of the task owner who will take action.
    - contact_ids (list of str): Required. List of Apollo contact IDs to assign tasks.
    - priority (str): Required. Task priority; one of 'high', 'medium', or 'low'.
    - due_at (str): Required. Task due date/time in ISO 8601 format (e.g., '2025-02-15T08:10:30Z').
    - type (str): Required. Task type, options include:
        - 'call'
        - 'outreach_manual_email'
        - 'linkedin_step_connect'
        - 'linkedin_step_message'
        - 'linkedin_step_view_profile'
        - 'linkedin_step_interact_post'
        - 'action_item'
    - status (str): Required. Task status; usually 'scheduled', or 'completed', 'archived'.
    - note (str): Optional. Additional context or description for the task.

    Returns:
    - Boolean true on success (no detailed response).

    Notes:
    - Requires a master API key.
    - No deduplication; duplicate tasks can be created.
    - Only available to paid Apollo plans.
    """

    url = "https://api.apollo.io/api/v1/tasks/bulk_create"
    headers = get_apollo_client()  # Needs master API key

    params = {
        "user_id": user_id,
        "contact_ids": contact_ids,
        "priority": priority,
        "due_at": due_at,
        "type": task_type,
        "status": status
    }

    if note:
        params["note"] = note

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=params)
            response.raise_for_status()
            return response.text  # should return "true"
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


async def apollo_search_tasks(
        sort_by_field: str = None,
        open_factor_names: list = None,
        page: int = 1,
        per_page: int = 50
) -> dict:
    """
    Search for tasks created by your team in Apollo with filtering and sorting options.

    Parameters:
    - sort_by_field (str): Optional. Sort tasks by:
        - 'task_due_at' (future-dated tasks first)
        - 'task_priority' (highest priority first)
    - open_factor_names (list of str): Optional. Provide task types to get counts of tasks by type.
    - page (int): Optional. Page number to retrieve.
    - per_page (int): Optional. Number of tasks per page.

    Returns:
    - List of tasks matching criteria, with pagination.
    - If open_factor_names is used, response includes task type counts.

    Notes:
    - Requires a master API key.
    - Limited to 50,000 records (100 per page, max 500 pages).
    - Not accessible to free Apollo users.
    """

    url = "https://api.apollo.io/api/v1/tasks/search"
    params = {
        "sort_by_field": sort_by_field,
        "page": page,
        "per_page": per_page
    }

    if open_factor_names:
        params["open_factor_names"] = open_factor_names

    headers = get_apollo_client()  # Needs master API key

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=params)
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
