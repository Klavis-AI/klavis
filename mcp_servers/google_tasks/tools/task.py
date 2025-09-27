from typing import List, Optional, Dict, Any
import asyncio
import logging
from googleapiclient.errors import HttpError
from .helpers import _get_service, _error_from_http 


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("google-tasks-mcp-server")

def list_task_lists() -> List[Dict[str, Any]]:
    try:
        service = _get_service()
        result = service.tasklists().list(maxResults=50).execute()
        return result.get("items", [])
    except HttpError as e:
        logger.exception("Error listing task lists")
        return _error_from_http(e, "Failed to list task lists")

def create_task_list(title: str) -> Dict[str, Any]:
    try:
        service = _get_service()
        return service.tasklists().insert(body={"title": title}).execute()
    except HttpError as e:
        logger.exception("Error creating task list")
        return _error_from_http(e, "Failed to create task list")

def list_tasks(task_list_id: str) -> List[Dict[str, Any]]:
    try:
        service = _get_service()
        result = service.tasks().list(tasklist=task_list_id).execute()
        return result.get("items", [])
    except HttpError as e:
        logger.exception("Error listing tasks")
        return _error_from_http(e, "Failed to list tasks")

def create_task(task_list_id: str, title: str, notes: str = "") -> Dict[str, Any]:
    try:
        service = _get_service()
        return service.tasks().insert(tasklist=task_list_id, body={"title": title, "notes": notes}).execute()
    except HttpError as e:
        logger.exception("Error creating task")
        return _error_from_http(e, "Failed to create task")

def update_task(
    task_list_id: str,
    task_id: str,
    title: Optional[str] = None,
    notes: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    try:
        service = _get_service()
        existing = service.tasks().get(tasklist=task_list_id, task=task_id).execute()
        if title is not None:
            existing["title"] = title
        if notes is not None:
            existing["notes"] = notes
        if status is not None:
            existing["status"] = status  # 'needsAction' or 'completed'
        return service.tasks().update(tasklist=task_list_id, task=task_id, body=existing).execute()
    except HttpError as e:
        logger.exception("Error updating task")
        return _error_from_http(e, "Failed to update task")

def delete_task(task_list_id: str, task_id: str) -> Dict[str, Any]:
    try:
        service = _get_service()
        service.tasks().delete(tasklist=task_list_id, task=task_id).execute()
        return {"status": "deleted"}
    except HttpError as e:
        logger.exception("Error deleting task")
        return _error_from_http(e, "Failed to delete task")

def find_task_list(title: str) -> List[Dict[str, Any]]:
    service = _get_service()
    items = service.tasklists().list(maxResults=100).execute().get("items", [])
    title_l = title.strip().lower()
    return [
        {"id": it["id"], "title": it.get("title", "")}
        for it in items
        if it.get("title", "").strip().lower() == title_l
    ]

def find_tasks_by_title(task_list_id: str, title: str, exact: bool = True) -> List[Dict[str, Any]]:
    service = _get_service()
    items = service.tasks().list(tasklist=task_list_id, showCompleted=True, showHidden=True).execute().get("items", [])
    t = title.strip()
    t_l = t.lower()
    out = []
    for it in items or []:
        name = it.get("title", "")
        ok = (name == t) if exact else (t_l in name.lower())
        if ok:
            out.append({"id": it["id"], "title": name, "status": it.get("status")})
    return out

def delete_task_by_title(task_list_id: str, title: str, strategy: str = "one", exact: bool = True) -> Dict[str, Any]:
    matches = find_tasks_by_title(task_list_id, title, exact)
    if strategy == "one":
        if len(matches) != 1:
            return {"error": f"Expected exactly one match, found {len(matches)}", "matches": matches}
        to_delete = [matches[0]["id"]]
    elif strategy == "first":
        if not matches:
            return {"deleted": [], "matches": []}
        to_delete = [matches[0]["id"]]
    elif strategy == "all":
        to_delete = [m["id"] for m in matches]
    else:
        return {"error": f"Unknown strategy '{strategy}'", "matches": matches}

    deleted = []
    for tid in to_delete:
        try:
            delete_task(task_list_id, tid)
            deleted.append(tid)
        except Exception as e:
            return {"error": str(e), "deleted": deleted, "remaining": to_delete[len(deleted):]}
    return {"deleted": deleted, "matches": matches}

def find_task_list_id_by_title(
    list_title: str,
    create_if_missing: bool = False,
) -> tuple[Optional[str], Dict[str, Any]]:
    """Return (task_list_id, meta). meta may contain error/created/matches."""
    lists = list_task_lists()
    if isinstance(lists, dict) and "error" in lists:
        return None, {"error": lists["error"]}

    matches = [l for l in lists if l.get("title") == list_title]
    if not matches:
        if create_if_missing:
            created = create_task_list(list_title)
            if isinstance(created, dict) and "id" in created:
                return created["id"], {"created": True}
            return None, {"error": "Failed to create list", "details": created}
        return None, {"error": "List not found", "candidates": [l.get("title") for l in lists]}

    if len(matches) > 1:
        return None, {
            "error": "List title is ambiguous",
            "matches": [{"id": l.get("id"), "title": l.get("title")} for l in matches],
        }

    return matches[0].get("id"), {}

