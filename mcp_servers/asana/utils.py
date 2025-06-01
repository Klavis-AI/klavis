import asyncio
import json
from collections.abc import Awaitable
from datetime import datetime
from functools import wraps
from typing import Any, Callable, TypeVar, cast

from constants import (
    ASANA_MAX_TIMEOUT_SECONDS,
    MAX_PROJECTS_TO_SCAN_BY_NAME,
    MAX_TAGS_TO_SCAN_BY_NAME,
    TASK_OPT_FIELDS,
    SortOrder,
    TaskSortBy,
)
from models import AsanaClient

ToolResponse = TypeVar("ToolResponse", bound=dict[str, Any])


# Exception classes (moved from exceptions.py)
class ToolExecutionError(Exception):
    def __init__(self, message: str, developer_message: str = ""):
        super().__init__(message)
        self.developer_message = developer_message


class AsanaToolExecutionError(ToolExecutionError):
    pass


class PaginationTimeoutError(AsanaToolExecutionError):
    def __init__(self, timeout_seconds: int, tool_name: str):
        message = f"Pagination timed out after {timeout_seconds} seconds"
        super().__init__(
            message=message,
            developer_message=f"{message} while calling the tool {tool_name}",
        )


# Decorator function (moved from decorators.py)
def clean_asana_response(func: Callable[..., Any]) -> Callable[..., Any]:
    def response_cleaner(data: dict[str, Any]) -> dict[str, Any]:
        if "gid" in data:
            data["id"] = data["gid"]
            del data["gid"]

        for k, v in data.items():
            if isinstance(v, dict):
                data[k] = response_cleaner(v)
            elif isinstance(v, list):
                data[k] = [
                    item if not isinstance(item, dict) else response_cleaner(item) for item in v
                ]

        return data

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        response = await func(*args, **kwargs)
        return response_cleaner(response)

    return wrapper


# Error class for retryable errors
class RetryableToolError(Exception):
    def __init__(self, message: str, additional_prompt_content: str = "", retry_after_ms: int = 1000, developer_message: str = ""):
        super().__init__(message)
        self.additional_prompt_content = additional_prompt_content
        self.retry_after_ms = retry_after_ms
        self.developer_message = developer_message


def remove_none_values(data: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in data.items() if v is not None}


def validate_date_format(name: str, date_str: str | None) -> None:
    if not date_str:
        return

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ToolExecutionError(f"Invalid {name} date format. Use the format YYYY-MM-DD.")


def build_task_search_query_params(
    keywords: str | None,
    completed: bool | None,
    assignee_id: str | None,
    project_id: str | None,
    team_id: str | None,
    tag_ids: list[str] | None,
    due_on: str | None,
    due_on_or_after: str | None,
    due_on_or_before: str | None,
    start_on: str | None,
    start_on_or_after: str | None,
    start_on_or_before: str | None,
    limit: int,
    sort_by: TaskSortBy,
    sort_order: SortOrder,
) -> dict[str, Any]:
    query_params: dict[str, Any] = {
        "text": keywords,
        "opt_fields": ",".join(TASK_OPT_FIELDS),
        "sort_by": sort_by.value,
        "sort_ascending": sort_order == SortOrder.ASCENDING,
        "limit": limit,
    }
    if completed is not None:
        query_params["completed"] = completed
    if assignee_id:
        query_params["assignee.any"] = assignee_id
    if project_id:
        query_params["projects.any"] = project_id
    if team_id:
        query_params["team.any"] = team_id
    if tag_ids:
        query_params["tags.any"] = ",".join(tag_ids)

    query_params = add_task_search_date_params(
        query_params,
        due_on,
        due_on_or_after,
        due_on_or_before,
        start_on,
        start_on_or_after,
        start_on_or_before,
    )

    return query_params


def add_task_search_date_params(
    query_params: dict[str, Any],
    due_on: str | None,
    due_on_or_after: str | None,
    due_on_or_before: str | None,
    start_on: str | None,
    start_on_or_after: str | None,
    start_on_or_before: str | None,
) -> dict[str, Any]:
    """
    Builds the date-related query parameters for task search.

    If a date is provided, it will be added to the query parameters. If not, it will be ignored.
    """
    if due_on:
        query_params["due_on"] = due_on
    if due_on_or_after:
        query_params["due_on.after"] = due_on_or_after
    if due_on_or_before:
        query_params["due_on.before"] = due_on_or_before
    if start_on:
        query_params["start_on"] = start_on
    if start_on_or_after:
        query_params["start_on.after"] = start_on_or_after
    if start_on_or_before:
        query_params["start_on.before"] = start_on_or_before

    return query_params


async def handle_new_task_associations(
    parent_task_id: str | None,
    project: str | None,
    workspace_id: str | None,
) -> tuple[str | None, str | None, str | None]:
    """
    Handles the association of a new task to a parent task, project, or workspace.

    If no association is provided, it will try to find a workspace in the user's account.
    In case the user has only one workspace, it will use that workspace.
    Otherwise, it will raise an error.

    If a workspace_id is not provided, but a parent_task_id or a project_id is provided, it will try
    to find the workspace associated with the parent task or project.

    In each of the two cases explained above, if a workspace is found, the function will return this
    value, even if the workspace_id argument was None.

    Returns a tuple of (parent_task_id, project_id, workspace_id).
    """
    project_id, project_name = (None, None)

    if project:
        if project.isnumeric():
            project_id = project
        else:
            project_name = project

    if project_name:
        project_data = await get_project_by_name_or_raise_error(project_name)
        project_id = project_data["id"]
        workspace_id = project_data["workspace"]["id"]

    if not any([parent_task_id, project_id, workspace_id]):
        workspace_id = await get_unique_workspace_id_or_raise_error()

    if not workspace_id and parent_task_id:
        # Import here to avoid circular imports
        from server import get_auth_token, get_asana_client
        
        access_token = get_auth_token()
        client = get_asana_client(access_token)
        response = await client.get(f"/tasks/{parent_task_id}", params={"opt_fields": "workspace"})
        workspace_id = response["data"]["workspace"]["id"]

    return parent_task_id, project_id, workspace_id


async def get_project_by_name_or_raise_error(
    project_name: str,
    max_items_to_scan: int = MAX_PROJECTS_TO_SCAN_BY_NAME,
) -> dict[str, Any]:
    response = await find_projects_by_name(
        names=[project_name],
        response_limit=100,
        max_items_to_scan=max_items_to_scan,
        return_projects_not_matched=True,
    )

    if not response["matches"]["projects"]:
        projects = response["not_matched"]["projects"]
        projects = [{"name": project["name"], "id": project["id"]} for project in projects]
        message = (
            f"Project with name '{project_name}' was not found. The search scans up to "
            f"{max_items_to_scan} projects. If the user account has a larger number of projects, "
            "it's possible that it exists, but the search didn't find it."
        )
        additional_prompt = f"Projects available: {json.dumps(projects)}"
        raise RetryableToolError(
            message=message,
            developer_message=f"{message} {additional_prompt}",
            additional_prompt_content=additional_prompt,
        )

    elif response["matches"]["count"] > 1:
        projects = [
            {"name": project["name"], "id": project["id"]}
            for project in response["matches"]["projects"]
        ]
        message = "Multiple projects found with the same name. Please provide a project ID instead."
        additional_prompt = f"Projects matching the name '{project_name}': {json.dumps(projects)}"
        raise RetryableToolError(
            message=message,
            developer_message=message,
            additional_prompt_content=additional_prompt,
        )

    return cast(dict, response["matches"]["projects"][0])


async def handle_new_task_tags(
    tags: list[str] | None,
    workspace_id: str | None,
) -> list[str] | None:
    if not tags:
        return None

    tag_ids = []
    tag_names = []
    for tag in tags:
        if tag.isnumeric():
            tag_ids.append(tag)
        else:
            tag_names.append(tag)

    if tag_names:
        response = await find_tags_by_name(tag_names)
        tag_ids.extend([tag["id"] for tag in response["matches"]["tags"]])

        if response["not_found"]["tags"]:
            # Import here to avoid circular imports
            from server import get_auth_token, get_asana_client
            
            access_token = get_auth_token()
            client = get_asana_client(access_token)
            
            created_tags = []
            for name in response["not_found"]["tags"]:
                tag_data = {"name": name, "workspace": workspace_id}
                create_response = await client.post("/tags", json_data={"data": tag_data})
                created_tags.append(create_response["data"]["id"])
            
            tag_ids.extend(created_tags)

    return tag_ids


async def get_tag_ids(
    tags: list[str] | None,
    max_items_to_scan: int = MAX_TAGS_TO_SCAN_BY_NAME,
) -> list[str] | None:
    """
    Returns the IDs of the tags provided in the tags list, which can be either tag IDs or tag names.

    If the tags list is empty, it returns None.
    """
    tag_ids = []
    tag_names = []

    if tags:
        for tag in tags:
            if tag.isnumeric():
                tag_ids.append(tag)
            else:
                tag_names.append(tag)

    if tag_names:
        searched_tags = await find_tags_by_name(
            tag_names,
            max_items_to_scan=max_items_to_scan,
            return_tags_not_matched=False,
        )
        tag_ids.extend([tag["id"] for tag in searched_tags["matches"]["tags"]])

    return tag_ids if tag_ids else None


async def paginate_tool_call(
    tool: Callable[[Any], Awaitable[ToolResponse]],
    response_key: str,
    max_items: int = 300,
    timeout_seconds: int = ASANA_MAX_TIMEOUT_SECONDS,
    next_page_token: str | None = None,
    **tool_kwargs: Any,
) -> list[ToolResponse]:
    """Paginate through tool calls to get all items."""
    items = []
    current_page_token = next_page_token

    async def paginate_loop() -> None:
        nonlocal current_page_token
        while len(items) < max_items:
            if current_page_token:
                tool_kwargs["next_page_token"] = current_page_token

            response = await tool(**tool_kwargs)
            response_items = response.get(response_key, [])
            items.extend(response_items)

            next_page = get_next_page(response)
            if not next_page.get("next_page_token"):
                break
            current_page_token = next_page["next_page_token"]

    try:
        await asyncio.wait_for(paginate_loop(), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise PaginationTimeoutError(timeout_seconds, tool.__name__)

    return items[:max_items]


async def get_unique_workspace_id_or_raise_error() -> str:
    # Import here to avoid circular imports
    from server import get_auth_token, get_asana_client
    
    access_token = get_auth_token()
    client = get_asana_client(access_token)
    
    response = await client.get("/workspaces")
    workspaces = response["data"]

    if len(workspaces) == 1:
        return workspaces[0]["id"]
    else:
        workspaces_info = [{"name": ws["name"], "id": ws["id"]} for ws in workspaces]
        message = "Multiple workspaces found. Please provide a workspace_id."
        additional_prompt = f"Available workspaces: {json.dumps(workspaces_info)}"
        raise RetryableToolError(
            message=message,
            developer_message=message,
            additional_prompt_content=additional_prompt,
        )


async def find_projects_by_name(
    names: list[str],
    team_id: list[str] | None = None,
    response_limit: int = 100,
    max_items_to_scan: int = MAX_PROJECTS_TO_SCAN_BY_NAME,
    return_projects_not_matched: bool = False,
) -> dict[str, Any]:
    """Find projects by name."""
    # Import here to avoid circular imports
    from server import get_auth_token, get_asana_client
    
    access_token = get_auth_token()
    client = get_asana_client(access_token)
    
    # Get all workspaces first
    workspaces_response = await client.get("/workspaces")
    workspaces = workspaces_response["data"]
    
    all_projects = []
    
    # Search through all workspaces
    for workspace in workspaces:
        projects_response = await client.get(
            f"/workspaces/{workspace['id']}/projects",
            params={"limit": min(response_limit, max_items_to_scan)}
        )
        all_projects.extend(projects_response["data"])
        
        if len(all_projects) >= max_items_to_scan:
            break
    
    # Match projects by name
    matches = []
    not_matched = []
    
    for name in names:
        found = False
        for project in all_projects:
            if project["name"].lower() == name.lower():
                matches.append(project)
                found = True
                break
        if not found:
            not_matched.append(name)
    
    result = {
        "matches": {
            "projects": matches,
            "count": len(matches)
        }
    }
    
    if return_projects_not_matched:
        result["not_matched"] = {
            "projects": all_projects,
            "tags": not_matched
        }
    
    return result


async def find_tags_by_name(
    names: list[str],
    workspace_id: list[str] | None = None,
    response_limit: int = 100,
    max_items_to_scan: int = MAX_TAGS_TO_SCAN_BY_NAME,
    return_tags_not_matched: bool = False,
) -> dict[str, Any]:
    """Find tags by name."""
    # Import here to avoid circular imports
    from server import get_auth_token, get_asana_client
    
    access_token = get_auth_token()
    client = get_asana_client(access_token)
    
    # Get all workspaces first
    if not workspace_id:
        workspaces_response = await client.get("/workspaces")
        workspaces = workspaces_response["data"]
    else:
        workspaces = [{"id": wid} for wid in workspace_id]
    
    all_tags = []
    
    # Search through all workspaces
    for workspace in workspaces:
        tags_response = await client.get(
            f"/workspaces/{workspace['id']}/tags",
            params={"limit": min(response_limit, max_items_to_scan)}
        )
        all_tags.extend(tags_response["data"])
        
        if len(all_tags) >= max_items_to_scan:
            break
    
    # Match tags by name
    matches = []
    not_found = []
    
    for name in names:
        found = False
        for tag in all_tags:
            if tag["name"].lower() == name.lower():
                matches.append(tag)
                found = True
                break
        if not found:
            not_found.append(name)
    
    result = {
        "matches": {
            "tags": matches,
            "count": len(matches)
        },
        "not_found": {
            "tags": not_found
        }
    }
    
    if return_tags_not_matched:
        result["not_matched"] = {
            "tags": all_tags
        }
    
    return result


def get_next_page(response: dict[str, Any]) -> dict[str, Any]:
    """Extract next page information from response."""
    next_page = response.get("next_page", {})
    return {
        "next_page_token": next_page.get("uri") if next_page else None
    } 