from __future__ import annotations

import base64
import datetime
import json
import logging
import os
from contextvars import ContextVar
from typing import Any, Dict, List, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .utils import (
    ValidationError,
    validate_task_data,
    parse_rfc3339,
    success,
    failure,
    shape_task,
    shape_task_list,
    http_error_to_message,
)

logger = logging.getLogger(__name__)

# Per-request (or per-stdio session) token storage
auth_token_context: ContextVar[str] = ContextVar("auth_token", default="")


# -------- Token helpers -------- #
def extract_access_token(request_or_scope) -> str:
    auth_data = os.getenv("AUTH_DATA")
    if not auth_data and request_or_scope is not None:
        try:
            if hasattr(request_or_scope, "headers"):
                header_val = request_or_scope.headers.get(
                    b"x-auth-data"
                ) or request_or_scope.headers.get("x-auth-data")
                if header_val:
                    if isinstance(header_val, bytes):
                        header_val = header_val.decode("utf-8")
                    auth_data = base64.b64decode(header_val).decode("utf-8")
            elif isinstance(request_or_scope, dict) and "headers" in request_or_scope:
                headers = dict(request_or_scope.get("headers", []))
                header_val = headers.get(b"x-auth-data") or headers.get("x-auth-data")
                if header_val:
                    if isinstance(header_val, bytes):
                        header_val = header_val.decode("utf-8")
                    auth_data = base64.b64decode(header_val).decode("utf-8")
        except Exception as e:
            logger.debug(f"Failed to pull x-auth-data header: {e}")

    if not auth_data:
        return ""
    try:
        auth_json = json.loads(auth_data)
        return auth_json.get("access_token", "") or ""
    except Exception as e:
        logger.warning(f"Failed to parse AUTH_DATA JSON: {e}")
        return ""


def get_auth_token() -> str:
    try:
        return auth_token_context.get()
    except LookupError:
        return ""


def get_tasks_service():
    """Get authenticated Google Tasks service."""
    token = get_auth_token()
    if not token:
        raise ValueError("No access token available")

    credentials = Credentials(token=token)
    return build("tasks", "v1", credentials=credentials)


# -------- Task List Operations -------- #
async def list_task_lists(
    max_results: int = 100, page_token: Optional[str] = None
) -> Dict[str, Any]:
    """List all task lists."""
    try:
        service = get_tasks_service()

        params = {"maxResults": max_results}
        if page_token:
            params["pageToken"] = page_token

        # Get task lists
        results = service.tasklists().list(**params).execute()
        task_lists = results.get("items", [])
        next_page_token = results.get("nextPageToken")

        shaped_lists = [shape_task_list(task_list) for task_list in task_lists]

        response_data = {"task_lists": shaped_lists, "total": len(shaped_lists)}

        if next_page_token:
            response_data["next_page_token"] = next_page_token

        return success(response_data)

    except HttpError as e:
        logger.error(f"Failed to list task lists: {e}")
        return failure(http_error_to_message(e), "api_error")
    except Exception as e:
        logger.error(f"Unexpected error listing task lists: {e}")
        return failure("Unexpected error occurred", "internal_error")


async def create_task_list(title: str) -> Dict[str, Any]:
    """Create/insert a new task list."""
    try:
        validate_task_data(title)

        service = get_tasks_service()

        task_list = {"title": title}
        result = service.tasklists().insert(body=task_list).execute()

        return success(shape_task_list(result), "Task list created successfully")

    except ValidationError as e:
        return failure(str(e), "validation_error")
    except HttpError as e:
        logger.error(f"Failed to create task list: {e}")
        return failure(http_error_to_message(e), "api_error")
    except Exception as e:
        logger.error(f"Unexpected error creating task list: {e}")
        return failure("Unexpected error occurred", "internal_error")


async def get_task_list(task_list_id: str) -> Dict[str, Any]:
    """Get a specific task list."""
    try:
        service = get_tasks_service()

        result = service.tasklists().get(tasklist=task_list_id).execute()

        return success(shape_task_list(result))

    except HttpError as e:
        logger.error(f"Failed to get task list {task_list_id}: {e}")
        return failure(http_error_to_message(e), "api_error")
    except Exception as e:
        logger.error(f"Unexpected error getting task list: {e}")
        return failure("Unexpected error occurred", "internal_error")


async def update_task_list(task_list_id: str, title: str) -> Dict[str, Any]:
    """Update a task list."""
    try:
        validate_task_data(title)

        service = get_tasks_service()

        task_list = {"id": task_list_id, "title": title}
        result = (
            service.tasklists().update(tasklist=task_list_id, body=task_list).execute()
        )

        return success(shape_task_list(result), "Task list updated successfully")

    except ValidationError as e:
        return failure(str(e), "validation_error")
    except HttpError as e:
        logger.error(f"Failed to update task list {task_list_id}: {e}")
        return failure(http_error_to_message(e), "api_error")
    except Exception as e:
        logger.error(f"Unexpected error updating task list: {e}")
        return failure("Unexpected error occurred", "internal_error")


async def delete_task_list(task_list_id: str) -> Dict[str, Any]:
    """Delete a task list."""
    try:
        service = get_tasks_service()

        service.tasklists().delete(tasklist=task_list_id).execute()

        return success(None, "Task list deleted successfully")

    except HttpError as e:
        logger.error(f"Failed to delete task list {task_list_id}: {e}")
        return failure(http_error_to_message(e), "api_error")
    except Exception as e:
        logger.error(f"Unexpected error deleting task list: {e}")
        return failure("Unexpected error occurred", "internal_error")


# -------- Task Operations -------- #
async def list_tasks(
    task_list_id: str,
    max_results: int = 100,
    show_completed: bool = True,
    show_deleted: bool = False,
    show_hidden: bool = False,
    page_token: Optional[str] = None,
    completed_max: Optional[str] = None,
    completed_min: Optional[str] = None,
    due_max: Optional[str] = None,
    due_min: Optional[str] = None,
    show_assigned: bool = False,
) -> Dict[str, Any]:
    """List tasks in a task list with comprehensive filtering options."""
    try:
        if completed_max:
            parse_rfc3339(completed_max)
        if completed_min:
            parse_rfc3339(completed_min)
        if due_max:
            parse_rfc3339(due_max)
        if due_min:
            parse_rfc3339(due_min)

        service = get_tasks_service()

        # Build query parameters
        params = {
            "maxResults": max_results,
            "showCompleted": show_completed,
            "showDeleted": show_deleted,
            "showHidden": show_hidden,
            "showAssigned": show_assigned,
        }

        if page_token:
            params["pageToken"] = page_token
        if completed_max:
            params["completedMax"] = completed_max
        if completed_min:
            params["completedMin"] = completed_min
        if due_max:
            params["dueMax"] = due_max
        if due_min:
            params["dueMin"] = due_min

        results = service.tasks().list(tasklist=task_list_id, **params).execute()
        tasks = results.get("items", [])
        next_page_token = results.get("nextPageToken")

        shaped_tasks = [shape_task(task) for task in tasks]

        response_data = {"tasks": shaped_tasks, "total": len(shaped_tasks)}

        if next_page_token:
            response_data["next_page_token"] = next_page_token

        return success(response_data)

    except HttpError as e:
        logger.error(f"Failed to list tasks: {e}")
        return failure(http_error_to_message(e), "api_error")
    except Exception as e:
        logger.error(f"Unexpected error listing tasks: {e}")
        return failure("Unexpected error occurred", "internal_error")


async def create_task(
    task_list_id: str,
    title: str,
    notes: Optional[str] = None,
    due: Optional[str] = None,
    parent: Optional[str] = None,
    previous: Optional[str] = None,
    status: Optional[str] = None,
    completed: Optional[str] = None,
    deleted: Optional[bool] = None,
) -> Dict[str, Any]:
    """Create a new task with comprehensive properties."""
    try:
        validate_task_data(title, notes, due, completed)

        service = get_tasks_service()

        task = {"title": title}
        if notes:
            task["notes"] = notes
        if due:
            task["due"] = due
        if parent:
            task["parent"] = parent
        if previous:
            task["previous"] = previous
        if status:
            task["status"] = status
        if completed:
            task["completed"] = completed
        if deleted is not None:
            task["deleted"] = deleted

        result = service.tasks().insert(tasklist=task_list_id, body=task).execute()

        return success(shape_task(result), "Task created successfully")

    except ValidationError as e:
        return failure(str(e), "validation_error")
    except HttpError as e:
        logger.error(f"Failed to create task: {e}")
        return failure(http_error_to_message(e), "api_error")
    except Exception as e:
        logger.error(f"Unexpected error creating task: {e}")
        return failure("Unexpected error occurred", "internal_error")


async def get_task(task_list_id: str, task_id: str) -> Dict[str, Any]:
    """Get a specific task."""
    try:
        service = get_tasks_service()

        result = service.tasks().get(tasklist=task_list_id, task=task_id).execute()

        return success(shape_task(result))

    except HttpError as e:
        logger.error(f"Failed to get task {task_id}: {e}")
        return failure(http_error_to_message(e), "api_error")
    except Exception as e:
        logger.error(f"Unexpected error getting task: {e}")
        return failure("Unexpected error occurred", "internal_error")


async def update_task(
    task_list_id: str,
    task_id: str,
    title: Optional[str] = None,
    notes: Optional[str] = None,
    due: Optional[str] = None,
    status: Optional[str] = None,
    completed: Optional[str] = None,
    deleted: Optional[bool] = None,
) -> Dict[str, Any]:
    """Update a task with comprehensive properties."""
    try:
        if title:
            validate_task_data(title, notes, due, completed)

        service = get_tasks_service()

        task = {"id": task_id}
        if title is not None:
            task["title"] = title
        if notes is not None:
            task["notes"] = notes
        if due is not None:
            task["due"] = due
        if status is not None:
            task["status"] = status
        if completed is not None:
            task["completed"] = completed
        if deleted is not None:
            task["deleted"] = deleted

        result = (
            service.tasks()
            .update(tasklist=task_list_id, task=task_id, body=task)
            .execute()
        )

        return success(shape_task(result), "Task updated successfully")

    except ValidationError as e:
        return failure(str(e), "validation_error")
    except HttpError as e:
        logger.error(f"Failed to update task {task_id}: {e}")
        return failure(http_error_to_message(e), "api_error")
    except Exception as e:
        logger.error(f"Unexpected error updating task: {e}")
        return failure("Unexpected error occurred", "internal_error")


async def delete_task(task_list_id: str, task_id: str) -> Dict[str, Any]:
    """Delete a task."""
    try:
        service = get_tasks_service()

        service.tasks().delete(tasklist=task_list_id, task=task_id).execute()

        return success(None, "Task deleted successfully")

    except HttpError as e:
        logger.error(f"Failed to delete task {task_id}: {e}")
        return failure(http_error_to_message(e), "api_error")
    except Exception as e:
        logger.error(f"Unexpected error deleting task: {e}")
        return failure("Unexpected error occurred", "internal_error")


async def move_task(
    task_list_id: str,
    task_id: str,
    parent: Optional[str] = None,
    previous: Optional[str] = None,
    destination_tasklist: Optional[str] = None,
) -> Dict[str, Any]:
    """Move a task to another position or to a different task list."""
    try:
        service = get_tasks_service()

        params = {}
        if parent is not None:
            params["parent"] = parent
        if previous is not None:
            params["previous"] = previous
        if destination_tasklist is not None:
            params["destinationTasklist"] = destination_tasklist

        result = (
            service.tasks()
            .move(tasklist=task_list_id, task=task_id, **params)
            .execute()
        )

        return success(shape_task(result), "Task moved successfully")

    except HttpError as e:
        logger.error(f"Failed to move task {task_id}: {e}")
        return failure(http_error_to_message(e), "api_error")
    except Exception as e:
        logger.error(f"Unexpected error moving task: {e}")
        return failure("Unexpected error occurred", "internal_error")


async def clear_completed_tasks(task_list_id: str) -> Dict[str, Any]:
    """Clear all completed tasks from a task list."""
    try:
        service = get_tasks_service()

        service.tasks().clear(tasklist=task_list_id).execute()

        return success(None, "Completed tasks cleared successfully")

    except HttpError as e:
        logger.error(f"Failed to clear completed tasks: {e}")
        return failure(http_error_to_message(e), "api_error")
    except Exception as e:
        logger.error(f"Unexpected error clearing completed tasks: {e}")
        return failure("Unexpected error occurred", "internal_error")


__all__ = [
    "auth_token_context",
    "extract_access_token",
    "get_auth_token",
    "list_task_lists",
    "create_task_list",
    "get_task_list",
    "update_task_list",
    "delete_task_list",
    "list_tasks",
    "create_task",
    "get_task",
    "update_task",
    "delete_task",
    "move_task",
    "clear_completed_tasks",
]
