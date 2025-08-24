"""
Handles all authentication and business logic for the Google Tasks API.

This module provides a non-interactive client and atomic functions to manage
task lists and tasks. It uses a Google Service Account for authentication.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

# Import the service_account module from google.oauth2
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Configuration ---
SCOPES = ["https://www.googleapis.com/auth/tasks"]
# The server will now look for this file for authentication.
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service-account.json")


# --- Google API Client & Auth ---

class GoogleTasksClient:
    """A non-interactive client for the Google Tasks API using a Service Account."""

    def __init__(self, key_file: str):
        self.key_file = key_file
        self._service = None

    def _get_credentials(self) -> service_account.Credentials:
        """
        Loads credentials from a service account key file.
        This is the standard, non-interactive way to authenticate for server-to-server communication.
        """
        if not os.path.exists(self.key_file):
            # Fail fast if the key file is missing.
            raise FileNotFoundError(
                f"Service account key file not found at '{self.key_file}'. "
                "Please follow the README to create and place it in the project root."
            )
        
        # Create credentials directly from the service account file.
        return service_account.Credentials.from_service_account_file(
            self.key_file, scopes=SCOPES
        )

    @property
    def service(self):
        """Provides an authenticated Google Tasks service object."""
        if self._service is None:
            credentials = self._get_credentials()
            self._service = build("tasks", "v1", credentials=credentials)
        return self._service


# --- Helper Functions ---

def _error_response(message: str, code: int = 400, hint: Optional[str] = None) -> Dict[str, Any]:
    """Creates a structured JSON error response for the AI to understand."""
    resp = {"ok": False, "error": {"message": message, "code": code}}
    if hint:
        resp["error"]["hint"] = hint
    return resp

def _call_api(api_call):
    """A single, central place to execute and handle errors from Google API calls."""
    try:
        return api_call.execute()
    except HttpError as e:
        try:
            error_details = json.loads(e.content).get("error", {})
            message = error_details.get("message", "An unknown API error occurred.")
            code = error_details.get("code", 500)
            if code == 404:
                raise FileNotFoundError("The requested Google Tasks resource was not found.")
            else:
                raise ConnectionError(f"Google API Error (Code {code}): {message}")
        except (json.JSONDecodeError, AttributeError):
             raise ConnectionError(f"Google API Error: {e}")


# --- Tool Implementations ---

# Create a single, reusable client instance for all tool functions.
client = GoogleTasksClient(SERVICE_ACCOUNT_FILE)

def list_task_lists(max_results: int = 50) -> Dict[str, Any]:
    """Returns a list of the user's task lists."""
    resp = _call_api(client.service.tasklists().list(maxResults=max_results))
    return {"ok": True, "task_lists": resp.get("items", [])}

def create_task_list(title: str) -> Dict[str, Any]:
    """Creates a new task list."""
    if not title or not title.strip():
        return _error_response("Title cannot be empty.", 400)
    body = {"title": title.strip()}
    resp = _call_api(client.service.tasklists().insert(body=body))
    return {"ok": True, "task_list": resp}

def list_tasks(list_id: str = "@default", show_completed: bool = True, max_results: int = 100) -> Dict[str, Any]:
    """Lists tasks within a given task list."""
    resp = _call_api(client.service.tasks().list(
        tasklist=list_id, showCompleted=show_completed, maxResults=max_results
    ))
    return {"ok": True, "tasks": resp.get("items", [])}

def create_task(list_id: str, title: str, notes: Optional[str] = None) -> Dict[str, Any]:
    """Creates a new task in a specified list."""
    if not title or not title.strip():
        return _error_response("Title cannot be empty.", 400)
    body = {"title": title.strip()}
    if notes:
        body["notes"] = notes
    resp = _call_api(client.service.tasks().insert(tasklist=list_id, body=body))
    return {"ok": True, "task": resp}

def update_task(list_id: str, task_id: str, title: Optional[str] = None, notes: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
    """Updates a task's fields using an efficient PATCH request."""
    patch_body = {}
    if title is not None:
        patch_body["title"] = title
    if notes is not None:
        patch_body["notes"] = notes
    if status is not None:
        patch_body["status"] = status

    if not patch_body:
        return _error_response("No fields provided to update.", 400)

    resp = _call_api(client.service.tasks().patch(tasklist=list_id, task=task_id, body=patch_body))
    return {"ok": True, "task": resp}

def delete_task(list_id: str, task_id: str) -> Dict[str, Any]:
    """Deletes a task by its ID."""
    # The Google API returns an empty response on successful deletion.
    _call_api(client.service.tasks().delete(tasklist=list_id, task=task_id))
    return {"ok": True, "deleted": True, "task_id": task_id}
