import asyncio
import json
from dataclasses import dataclass
import logging
from typing import Any, Dict, Optional, cast
from contextvars import ContextVar
from functools import wraps

import httpx

from .constants import ASANA_API_VERSION, ASANA_BASE_URL, ASANA_MAX_CONCURRENT_REQUESTS, ASANA_MAX_TIMEOUT_SECONDS

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Response Normalization Utilities
# ============================================================================

def get_path(data: Dict, path: str) -> Any:
    """Safe dot-notation access. Returns None if path fails."""
    if not data:
        return None
    current = data
    for key in path.split('.'):
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    return current


def normalize(source: Dict, mapping: Dict[str, Any]) -> Dict:
    """
    Creates a new clean dictionary based strictly on the mapping rules.
    Excludes fields with None/null values from the output.
    Args:
        source: Raw vendor JSON.
        mapping: Dict of { "TargetFieldName": "Source.Path" OR Lambda_Function }
    """
    clean_data = {}
    for target_key, rule in mapping.items():
        value = None
        if isinstance(rule, str):
            value = get_path(source, rule)
        elif callable(rule):
            try:
                value = rule(source)
            except Exception:
                value = None
        if value is not None:
            clean_data[target_key] = value
    return clean_data


# ============================================================================
# Normalization Mapping Rules
# ============================================================================

# User normalization rules
USER_RULES = {
    "id": "id",
    "name": "name",
    "email": "email",
    "photo": "photo",
    "workspaces": lambda x: [
        normalize(ws, WORKSPACE_COMPACT_RULES) for ws in x.get("workspaces", [])
    ] if x.get("workspaces") else None,
}

USER_COMPACT_RULES = {
    "id": "id",
    "name": "name",
}

# Workspace normalization rules
WORKSPACE_RULES = {
    "id": "id",
    "name": "name",
    "emailDomains": "email_domains",
    "isOrganization": "is_organization",
}

WORKSPACE_COMPACT_RULES = {
    "id": "id",
    "name": "name",
}

# Team normalization rules
TEAM_RULES = {
    "id": "id",
    "name": "name",
    "description": "description",
    "organization": lambda x: normalize(x.get("organization", {}), WORKSPACE_COMPACT_RULES) if x.get("organization") else None,
    "url": "permalink_url",
}

TEAM_COMPACT_RULES = {
    "id": "id",
    "name": "name",
}

# Tag normalization rules
TAG_RULES = {
    "id": "id",
    "name": "name",
    "color": "color",
    "description": "notes",
    "workspace": lambda x: normalize(x.get("workspace", {}), WORKSPACE_COMPACT_RULES) if x.get("workspace") else None,
}

TAG_COMPACT_RULES = {
    "id": "id",
    "name": "name",
}

# Project normalization rules
PROJECT_RULES = {
    "id": "id",
    "name": "name",
    "description": "notes",
    "color": "color",
    "isCompleted": "completed",
    "completedAt": "completed_at",
    "completedBy": lambda x: normalize(x.get("completed_by", {}), USER_COMPACT_RULES) if x.get("completed_by") else None,
    "createdAt": "created_at",
    "modifiedAt": "modified_at",
    "dueDate": "due_on",
    "owner": lambda x: normalize(x.get("owner", {}), USER_COMPACT_RULES) if x.get("owner") else None,
    "team": lambda x: normalize(x.get("team", {}), TEAM_COMPACT_RULES) if x.get("team") else None,
    "workspace": lambda x: normalize(x.get("workspace", {}), WORKSPACE_COMPACT_RULES) if x.get("workspace") else None,
    "url": "permalink_url",
    "statusUpdate": "current_status_update",
    "members": lambda x: [
        normalize(m, USER_COMPACT_RULES) for m in x.get("members", [])
    ] if x.get("members") else None,
}

PROJECT_COMPACT_RULES = {
    "id": "id",
    "name": "name",
}

# Membership normalization rules
MEMBERSHIP_RULES = {
    "project": lambda x: normalize(x.get("project", {}), PROJECT_COMPACT_RULES) if x.get("project") else None,
    "section": lambda x: {"id": x.get("section", {}).get("id"), "name": x.get("section", {}).get("name")} if x.get("section") else None,
}

# Task normalization rules
TASK_RULES = {
    "id": "id",
    "name": "name",
    "description": "notes",
    "isCompleted": "completed",
    "completedAt": "completed_at",
    "completedBy": lambda x: normalize(x.get("completed_by", {}), USER_COMPACT_RULES) if x.get("completed_by") else None,
    "createdAt": "created_at",
    "createdBy": lambda x: normalize(x.get("created_by", {}), USER_COMPACT_RULES) if x.get("created_by") else None,
    "dueDate": "due_on",
    "startDate": "start_on",
    "assignee": lambda x: normalize(x.get("assignee", {}), USER_COMPACT_RULES) if x.get("assignee") else None,
    "assigneeStatus": "assignee_status",
    "approvalStatus": "approval_status",
    "subtaskCount": "num_subtasks",
    "parent": lambda x: {"id": x.get("parent", {}).get("id"), "name": x.get("parent", {}).get("name")} if x.get("parent") else None,
    "workspace": lambda x: normalize(x.get("workspace", {}), WORKSPACE_COMPACT_RULES) if x.get("workspace") else None,
    "url": "permalink_url",
    "tags": lambda x: [
        normalize(t, TAG_COMPACT_RULES) for t in x.get("tags", [])
    ] if x.get("tags") else None,
    "memberships": lambda x: [
        normalize(m, MEMBERSHIP_RULES) for m in x.get("memberships", [])
    ] if x.get("memberships") else None,
    "dependencies": lambda x: [
        {"id": d.get("id")} for d in x.get("dependencies", [])
    ] if x.get("dependencies") else None,
    "dependents": lambda x: [
        {"id": d.get("id")} for d in x.get("dependents", [])
    ] if x.get("dependents") else None,
}

# Attachment normalization rules
ATTACHMENT_RULES = {
    "id": "id",
    "name": "name",
    "url": "download_url",
    "host": "host",
    "viewUrl": "view_url",
    "createdAt": "created_at",
    "parent": lambda x: {"id": x.get("parent", {}).get("id")} if x.get("parent") else None,
}


def normalize_task(raw_task: Dict) -> Dict:
    """Normalize a single task."""
    return normalize(raw_task, TASK_RULES)


def normalize_project(raw_project: Dict) -> Dict:
    """Normalize a single project."""
    return normalize(raw_project, PROJECT_RULES)


def normalize_workspace(raw_workspace: Dict) -> Dict:
    """Normalize a single workspace."""
    return normalize(raw_workspace, WORKSPACE_RULES)


def normalize_user(raw_user: Dict) -> Dict:
    """Normalize a single user."""
    return normalize(raw_user, USER_RULES)


def normalize_team(raw_team: Dict) -> Dict:
    """Normalize a single team."""
    return normalize(raw_team, TEAM_RULES)


def normalize_tag(raw_tag: Dict) -> Dict:
    """Normalize a single tag."""
    return normalize(raw_tag, TAG_RULES)


def normalize_attachment(raw_attachment: Dict) -> Dict:
    """Normalize a single attachment."""
    return normalize(raw_attachment, ATTACHMENT_RULES)

# Context variable to store the access token for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

# Type definitions
ToolResponse = dict[str, Any]

# Exception classes (moved from utils.py)
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


class RetryableToolError(Exception):
    def __init__(self, message: str, additional_prompt_content: str = "", retry_after_ms: int = 1000, developer_message: str = ""):
        super().__init__(message)
        self.additional_prompt_content = additional_prompt_content
        self.retry_after_ms = retry_after_ms
        self.developer_message = developer_message


# Utility functions (moved from utils.py)
def remove_none_values(data: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in data.items() if v is not None}


def get_next_page(response: dict[str, Any]) -> dict[str, Any]:
    """Extract next page information from response."""
    next_page = response.get("next_page", {})
    return {
        "next_page_token": next_page.get("uri") if next_page else None
    }


# Decorator function (moved from utils.py)
def clean_asana_response(func):
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


async def get_unique_workspace_id_or_raise_error() -> str:
    client = get_asana_client()
    
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


@dataclass
class AsanaClient:
    auth_token: str
    base_url: str = ASANA_BASE_URL
    api_version: str = ASANA_API_VERSION
    max_concurrent_requests: int = ASANA_MAX_CONCURRENT_REQUESTS
    _semaphore: asyncio.Semaphore | None = None

    def __post_init__(self) -> None:
        self._semaphore = self._semaphore or asyncio.Semaphore(self.max_concurrent_requests)

    def _build_url(self, endpoint: str, api_version: str | None = None) -> str:
        api_version = api_version or self.api_version
        return f"{self.base_url.rstrip('/')}/{api_version.strip('/')}/{endpoint.lstrip('/')}"

    def _build_error_messages(self, response: httpx.Response) -> tuple[str, str]:
        try:
            data = response.json()
            errors = data["errors"]

            if len(errors) == 1:
                error_message = errors[0]["message"]
                developer_message = (
                    f"{errors[0]['message']} | {errors[0]['help']} "
                    f"(HTTP status code: {response.status_code})"
                )
            else:
                errors_concat = "', '".join([error["message"] for error in errors])
                error_message = f"Multiple errors occurred: '{errors_concat}'"
                developer_message = (
                    f"Multiple errors occurred: {json.dumps(errors)} "
                    f"(HTTP status code: {response.status_code})"
                )

        except Exception as e:
            error_message = "Failed to parse Asana error response"
            developer_message = f"Failed to parse Asana error response: {type(e).__name__}: {e!s}"

        return error_message, developer_message

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code < 300:
            return

        error_message, developer_message = self._build_error_messages(response)

        raise AsanaToolExecutionError(error_message, developer_message)

    def _set_request_body(self, kwargs: dict, data: dict | None, json_data: dict | None) -> dict:
        if data and json_data:
            raise ValueError("Cannot provide both data and json_data")

        if data:
            kwargs["data"] = data

        elif json_data:
            kwargs["json"] = json_data

        return kwargs

    @clean_asana_response
    async def get(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        api_version: str | None = None,
    ) -> dict:
        default_headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Accept": "application/json",
        }
        headers = {**default_headers, **(headers or {})}

        kwargs = {
            "url": self._build_url(endpoint, api_version),
            "headers": headers,
        }

        if params:
            kwargs["params"] = params

        async with self._semaphore, httpx.AsyncClient() as client:  # type: ignore[union-attr]
            response = await client.get(**kwargs)  # type: ignore[arg-type]
            self._raise_for_status(response)
        return cast(dict, response.json())

    @clean_asana_response
    async def post(
        self,
        endpoint: str,
        data: Optional[dict] = None,
        json_data: Optional[dict] = None,
        files: Optional[dict] = None,
        headers: Optional[dict] = None,
        api_version: str | None = None,
    ) -> dict:
        default_headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Accept": "application/json",
        }

        if files is None and json_data is not None:
            default_headers["Content-Type"] = "application/json"

        headers = {**default_headers, **(headers or {})}

        kwargs = {
            "url": self._build_url(endpoint, api_version),
            "headers": headers,
        }

        if files is not None:
            kwargs["files"] = files
            if data is not None:
                kwargs["data"] = data
        else:
            kwargs = self._set_request_body(kwargs, data, json_data)

        async with self._semaphore, httpx.AsyncClient() as client:  # type: ignore[union-attr]
            response = await client.post(**kwargs)  # type: ignore[arg-type]
            self._raise_for_status(response)
        return cast(dict, response.json())

    @clean_asana_response
    async def put(
        self,
        endpoint: str,
        data: Optional[dict] = None,
        json_data: Optional[dict] = None,
        headers: Optional[dict] = None,
        api_version: str | None = None,
    ) -> dict:
        headers = headers or {}
        headers["Authorization"] = f"Bearer {self.auth_token}"
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"

        kwargs = {
            "url": self._build_url(endpoint, api_version),
            "headers": headers,
        }

        kwargs = self._set_request_body(kwargs, data, json_data)

        async with self._semaphore, httpx.AsyncClient() as client:  # type: ignore[union-attr]
            response = await client.put(**kwargs)  # type: ignore[arg-type]
            self._raise_for_status(response)
        return cast(dict, response.json())

    async def get_current_user(self) -> dict:
        response = await self.get("/users/me")
        return cast(dict, response["data"]) 


def get_asana_client() -> AsanaClient:
    """Create Asana client with access token from context."""
    access_token = get_auth_token()
    return AsanaClient(auth_token=access_token)

def get_auth_token() -> str:
    """Get the authentication token from context."""
    try:
        return auth_token_context.get()
    except LookupError:
        raise RuntimeError("Authentication token not found in request context") 