import base64
from typing import Annotated, Any, Dict, cast
import logging
import json
from datetime import datetime

from .constants import TASK_OPT_FIELDS, SortOrder, TaskSortBy, MAX_PROJECTS_TO_SCAN_BY_NAME, MAX_TAGS_TO_SCAN_BY_NAME
from .base import (
    get_asana_client,
    get_next_page,
    remove_none_values,
    get_unique_workspace_id_or_raise_error,
    AsanaToolExecutionError,
    RetryableToolError,
)

logger = logging.getLogger(__name__)


def validate_date_format(name: str, date_str: str | None) -> None:
    if not date_str:
        return

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise AsanaToolExecutionError(f"Invalid {name} date format. Use the format YYYY-MM-DD.")


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
        client = get_asana_client()
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
            client = get_asana_client()
            
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


async def find_projects_by_name(
    names: list[str],
    team_id: list[str] | None = None,
    response_limit: int = 100,
    max_items_to_scan: int = MAX_PROJECTS_TO_SCAN_BY_NAME,
    return_projects_not_matched: bool = False,
) -> dict[str, Any]:
    """Find projects by name."""
    client = get_asana_client()
    
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
    client = get_asana_client()
    
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

async def search_tasks(
    keywords: str | None = None,
    workspace_id: str | None = None,
    assignee_id: str | None = None,
    project: str | None = None,
    team_id: str | None = None,
    tags: list[str] | None = None,
    due_on: str | None = None,
    due_on_or_after: str | None = None,
    due_on_or_before: str | None = None,
    start_on: str | None = None,
    start_on_or_after: str | None = None,
    start_on_or_before: str | None = None,
    completed: bool | None = None,
    limit: int = 100,
    sort_by: TaskSortBy = TaskSortBy.MODIFIED_AT,
    sort_order: SortOrder = SortOrder.DESCENDING,
) -> Dict[str, Any]:
    """Search for tasks"""
    try:
        limit = max(1, min(100, limit))
        project_id = None

        if project:
            if project.isnumeric():
                project_id = project
            else:
                project_data = await get_project_by_name_or_raise_error(project)
                project_id = project_data["id"]
                if not workspace_id:
                    workspace_id = project_data["workspace"]["id"]

        tag_ids = await get_tag_ids(tags)

        client = get_asana_client()

        validate_date_format("due_on", due_on)
        validate_date_format("due_on_or_after", due_on_or_after)
        validate_date_format("due_on_or_before", due_on_or_before)
        validate_date_format("start_on", start_on)
        validate_date_format("start_on_or_after", start_on_or_after)
        validate_date_format("start_on_or_before", start_on_or_before)

        if not any([workspace_id, project_id, team_id]):
            workspace_id = await get_unique_workspace_id_or_raise_error()

        if not workspace_id and team_id:
            from .teams import get_team_by_id
            team = await get_team_by_id(team_id)
            workspace_id = team["organization"]["id"]

        response = await client.get(
            f"/workspaces/{workspace_id}/tasks/search",
            params=build_task_search_query_params(
                keywords=keywords,
                completed=completed,
                assignee_id=assignee_id,
                project_id=project_id,
                team_id=team_id,
                tag_ids=tag_ids,
                due_on=due_on,
                due_on_or_after=due_on_or_after,
                due_on_or_before=due_on_or_before,
                start_on=start_on,
                start_on_or_after=start_on_or_after,
                start_on_or_before=start_on_or_before,
                limit=limit,
                sort_by=sort_by,
                sort_order=sort_order,
            ),
        )

        tasks_by_id = {task["id"]: task for task in response["data"]}
        tasks = list(tasks_by_id.values())

        return {"tasks": tasks, "count": len(tasks)}

    except AsanaToolExecutionError as e:
        logger.error(f"Asana API error: {e}")
        raise RuntimeError(f"Asana API Error: {e}")
    except Exception as e:
        logger.exception(f"Error executing search_tasks: {e}")
        raise e


async def get_task_by_id(
    task_id: str,
    max_subtasks: int = 100,
) -> Dict[str, Any]:
    """Get a task by its ID"""
    try:
        client = get_asana_client()
        response = await client.get(
            f"/tasks/{task_id}",
            params={"opt_fields": ",".join(TASK_OPT_FIELDS)},
        )
        if max_subtasks > 0:
            max_subtasks = min(max_subtasks, 100)
            subtasks = await get_subtasks_from_a_task(task_id=task_id, limit=max_subtasks)
            response["data"]["subtasks"] = subtasks["subtasks"]
        return {"task": response["data"]}

    except AsanaToolExecutionError as e:
        logger.error(f"Asana API error: {e}")
        raise RuntimeError(f"Asana API Error: {e}")
    except Exception as e:
        logger.exception(f"Error executing get_task_by_id: {e}")
        raise e


async def get_subtasks_from_a_task(
    task_id: str,
    limit: int = 100,
    next_page_token: str | None = None,
) -> Dict[str, Any]:
    """Get subtasks from a task"""
    try:
        limit = max(1, min(100, limit))
        client = get_asana_client()
        response = await client.get(
            f"/tasks/{task_id}/subtasks",
            params=remove_none_values({
                "limit": limit,
                "offset": next_page_token,
                "opt_fields": ",".join(TASK_OPT_FIELDS),
            }),
        )

        return {
            "subtasks": response["data"],
            "count": len(response["data"]),
            "next_page": get_next_page(response),
        }

    except AsanaToolExecutionError as e:
        logger.error(f"Asana API error: {e}")
        raise RuntimeError(f"Asana API Error: {e}")
    except Exception as e:
        logger.exception(f"Error executing get_subtasks_from_a_task: {e}")
        raise e


async def update_task(
    task_id: str,
    name: str | None = None,
    completed: bool | None = None,
    start_date: str | None = None,
    due_date: str | None = None,
    description: str | None = None,
    assignee_id: str | None = None,
) -> Dict[str, Any]:
    """Update a task in Asana"""
    try:
        client = get_asana_client()

        validate_date_format("start_date", start_date)
        validate_date_format("due_date", due_date)

        update_data = remove_none_values({
            "name": name,
            "completed": completed,
            "start_on": start_date,
            "due_on": due_date,
            "notes": description,
            "assignee": assignee_id,
        })

        response = await client.put(f"/tasks/{task_id}", json_data={"data": update_data})
        return {"task": response["data"]}

    except AsanaToolExecutionError as e:
        logger.error(f"Asana API error: {e}")
        raise RuntimeError(f"Asana API Error: {e}")
    except Exception as e:
        logger.exception(f"Error executing update_task: {e}")
        raise e


async def mark_task_as_completed(
    task_id: str,
) -> Dict[str, Any]:
    """Mark a task as completed"""
    return await update_task(task_id, completed=True)


async def create_task(
    name: str,
    start_date: str | None = None,
    due_date: str | None = None,
    description: str | None = None,
    parent_task_id: str | None = None,
    workspace_id: str | None = None,
    project: str | None = None,
    assignee_id: str | None = "me",
    tags: list[str] | None = None,
) -> Dict[str, Any]:
    """Create a task in Asana"""
    try:
        client = get_asana_client()

        validate_date_format("start_date", start_date)
        validate_date_format("due_date", due_date)

        parent_task_id, project_id, workspace_id = await handle_new_task_associations(
            parent_task_id, project, workspace_id
        )

        tag_ids = await handle_new_task_tags(tags, workspace_id)

        task_data = remove_none_values({
            "name": name,
            "notes": description,
            "start_on": start_date,
            "due_on": due_date,
            "assignee": assignee_id,
            "parent": parent_task_id,
            "projects": [project_id] if project_id else None,
            "workspace": workspace_id,
            "tags": tag_ids,
        })

        response = await client.post("/tasks", json_data={"data": task_data})
        return {"task": response["data"]}

    except AsanaToolExecutionError as e:
        logger.error(f"Asana API error: {e}")
        raise RuntimeError(f"Asana API Error: {e}")
    except Exception as e:
        logger.exception(f"Error executing create_task: {e}")
        raise e


async def attach_file_to_task(
    task_id: str,
    file_name: str,
    file_content_str: str | None = None,
    file_content_base64: str | None = None,
    file_content_url: str | None = None,
    file_encoding: str = "utf-8",
) -> Dict[str, Any]:
    """Attach a file to a task"""
    try:
        client = get_asana_client()

        if not any([file_content_str, file_content_base64, file_content_url]):
            raise ValueError("One of file_content_str, file_content_base64, or file_content_url must be provided")

        if file_content_url:
            # External URL attachment
            attachment_data = {
                "name": file_name,
                "url": file_content_url,
                "parent": task_id,
            }
            response = await client.post("/attachments", json_data={"data": attachment_data})
        else:
            # File upload
            if file_content_str:
                file_content = file_content_str.encode(file_encoding)
            elif file_content_base64:
                file_content = base64.b64decode(file_content_base64)

            files = {
                "file": (file_name, file_content)
            }
            data = {"parent": task_id}
            
            response = await client.post("/attachments", data=data, files=files)

        return {"attachment": response["data"]}

    except AsanaToolExecutionError as e:
        logger.error(f"Asana API error: {e}")
        raise RuntimeError(f"Asana API Error: {e}")
    except Exception as e:
        logger.exception(f"Error executing attach_file_to_task: {e}")
        raise e
