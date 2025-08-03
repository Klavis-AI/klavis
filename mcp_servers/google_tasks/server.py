import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def _get_service():
    creds = Credentials(
        None,
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    )
    return build("tasks", "v1", credentials=creds)

def list_task_lists():
    """List all task lists for the user."""
    service = _get_service()
    results = service.tasklists().list(maxResults=10).execute()
    return results.get("items", [])

def create_task_list(title: str):
    """Create a new task list with the given title."""
    service = _get_service()
    body = {"title": title}
    result = service.tasklists().insert(body=body).execute()
    return result

def list_tasks(task_list_id: str):
    """List tasks from a specific task list."""
    service = _get_service()
    results = service.tasks().list(tasklist=task_list_id).execute()
    return results.get("items", [])

def create_task(task_list_id: str, title: str, notes: str = ""):
    """Create a new task in a task list."""
    service = _get_service()
    task = {"title": title, "notes": notes}
    result = service.tasks().insert(tasklist=task_list_id, body=task).execute()
    return result

def update_task(task_list_id: str, task_id: str, title: str = None, notes: str = None, status: str = None):
    """Update fields of an existing task."""
    service = _get_service()
    existing_task = service.tasks().get(tasklist=task_list_id, task=task_id).execute()
    if title:
        existing_task["title"] = title
    if notes:
        existing_task["notes"] = notes
    if status:
        existing_task["status"] = status
    updated = service.tasks().update(tasklist=task_list_id, task=task_id, body=existing_task).execute()
    return updated

def delete_task(task_list_id: str, task_id: str):
    """Delete a task by ID."""
    service = _get_service()
    service.tasks().delete(tasklist=task_list_id, task=task_id).execute()
    return {"status": "deleted"}
