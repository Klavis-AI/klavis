import base64
from typing import Annotated, Any, Dict
import logging

from constants import TASK_OPT_FIELDS, SortOrder, TaskSortBy
from models import AsanaClient
from utils import (
    build_task_search_query_params,
    get_next_page,
    get_project_by_name_or_raise_error,
    get_tag_ids,
    get_unique_workspace_id_or_raise_error,
    handle_new_task_associations,
    handle_new_task_tags,
    remove_none_values,
    validate_date_format,
    AsanaToolExecutionError,
)

logger = logging.getLogger(__name__)


async def search_tasks(
    access_token: str,
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

        client = AsanaClient(auth_token=access_token)

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
            team = await get_team_by_id(access_token, team_id)
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
    access_token: str,
    task_id: str,
    max_subtasks: int = 100,
) -> Dict[str, Any]:
    """Get a task by its ID"""
    try:
        client = AsanaClient(auth_token=access_token)
        response = await client.get(
            f"/tasks/{task_id}",
            params={"opt_fields": ",".join(TASK_OPT_FIELDS)},
        )
        if max_subtasks > 0:
            max_subtasks = min(max_subtasks, 100)
            subtasks = await get_subtasks_from_a_task(access_token, task_id=task_id, limit=max_subtasks)
            response["data"]["subtasks"] = subtasks["subtasks"]
        return {"task": response["data"]}

    except AsanaToolExecutionError as e:
        logger.error(f"Asana API error: {e}")
        raise RuntimeError(f"Asana API Error: {e}")
    except Exception as e:
        logger.exception(f"Error executing get_task_by_id: {e}")
        raise e


async def get_subtasks_from_a_task(
    access_token: str,
    task_id: str,
    limit: int = 100,
    next_page_token: str | None = None,
) -> Dict[str, Any]:
    """Get subtasks from a task"""
    try:
        limit = max(1, min(100, limit))
        client = AsanaClient(auth_token=access_token)
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
    access_token: str,
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
        client = AsanaClient(auth_token=access_token)

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
    access_token: str,
    task_id: str,
) -> Dict[str, Any]:
    """Mark a task as completed"""
    return await update_task(access_token, task_id, completed=True)


async def create_task(
    access_token: str,
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
        client = AsanaClient(auth_token=access_token)

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
    access_token: str,
    task_id: str,
    file_name: str,
    file_content_str: str | None = None,
    file_content_base64: str | None = None,
    file_content_url: str | None = None,
    file_encoding: str = "utf-8",
) -> Dict[str, Any]:
    """Attach a file to a task"""
    try:
        client = AsanaClient(auth_token=access_token)

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
