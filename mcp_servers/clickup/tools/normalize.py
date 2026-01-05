"""
Response normalization utilities for ClickUp MCP Server.
Transforms raw vendor responses into Klavis-defined schemas.
"""

from typing import Any, Dict, List, Optional


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


# ====================
# Mapping Rules
# ====================

USER_RULES = {
    "id": "id",
    "username": "username",
    "email": "email",
    "displayName": lambda x: x.get("username") or x.get("email"),
    "avatarUrl": "profilePicture",
    "initials": "initials",
    "color": "color",
}

MEMBER_RULES = {
    "id": "user.id",
    "username": "user.username",
    "email": "user.email",
    "displayName": lambda x: get_path(x, "user.username") or get_path(x, "user.email"),
    "avatarUrl": "user.profilePicture",
    "initials": "user.initials",
    "role": "role",
}

TEAM_RULES = {
    "id": "id",
    "name": "name",
    "color": "color",
    "avatarUrl": "avatar",
    "members": lambda x: [
        normalize(m, MEMBER_RULES) for m in x.get("members", [])
    ] if x.get("members") else None,
}

SPACE_RULES = {
    "id": "id",
    "name": "name",
    "isPrivate": "private",
    "color": "color",
    "isArchived": "archived",
}

FOLDER_RULES = {
    "id": "id",
    "name": "name",
    "isHidden": "hidden",
    "isArchived": "archived",
    "spaceId": "space.id",
    "taskCount": "task_count",
}

STATUS_RULES = {
    "id": "id",
    "name": "status",
    "color": "color",
    "type": "type",
    "orderIndex": "orderindex",
}

LIST_RULES = {
    "id": "id",
    "name": "name",
    "description": "content",
    "isArchived": "archived",
    "folderId": "folder.id",
    "spaceId": "space.id",
    "taskCount": "task_count",
    "dueDate": "due_date",
    "startDate": "start_date",
    "priority": "priority.priority",
    "statuses": lambda x: [
        normalize(s, STATUS_RULES) for s in x.get("statuses", [])
    ] if x.get("statuses") else None,
}

ASSIGNEE_RULES = {
    "id": "id",
    "username": "username",
    "email": "email",
    "displayName": lambda x: x.get("username") or x.get("email"),
    "avatarUrl": "profilePicture",
    "initials": "initials",
}

TAG_RULES = {
    "name": "name",
    "color": "tag_bg",
    "textColor": "tag_fg",
}

PRIORITY_RULES = {
    "level": "priority",
    "color": "color",
}

TASK_RULES = {
    "id": "id",
    "customId": "custom_id",
    "name": "name",
    "description": "description",
    "textContent": "text_content",
    "status": "status.status",
    "statusColor": "status.color",
    "createdAt": "date_created",
    "updatedAt": "date_updated",
    "closedAt": "date_closed",
    "doneAt": "date_done",
    "dueDate": "due_date",
    "startDate": "start_date",
    "timeEstimate": "time_estimate",
    "timeSpent": lambda x: get_path(x, "time_spent.time") or x.get("time_spent"),
    "url": "url",
    "isArchived": "archived",
    "listId": "list.id",
    "listName": "list.name",
    "folderId": "folder.id",
    "folderName": "folder.name",
    "spaceId": "space.id",
    "parentTaskId": "parent",
    "priority": lambda x: x.get("priority", {}).get("priority") if isinstance(x.get("priority"), dict) else x.get("priority"),
    "priorityColor": "priority.color",
    "creator": lambda x: normalize(x.get("creator", {}), ASSIGNEE_RULES) if x.get("creator") else None,
    "assignees": lambda x: [
        normalize(a, ASSIGNEE_RULES) for a in x.get("assignees", [])
    ] if x.get("assignees") else None,
    "tags": lambda x: [
        normalize(t, TAG_RULES) for t in x.get("tags", [])
    ] if x.get("tags") else None,
    "subtasks": lambda x: [
        normalize_task(s) for s in x.get("subtasks", [])
    ] if x.get("subtasks") else None,
}

COMMENT_RULES = {
    "id": "id",
    "text": lambda x: x.get("comment_text") or x.get("text_content") or (
        x.get("comment") if isinstance(x.get("comment"), str) else None
    ),
    "createdAt": "date",
    "isResolved": "resolved",
    "author": lambda x: normalize(x.get("user", {}), ASSIGNEE_RULES) if x.get("user") else None,
    "assignee": lambda x: normalize(x.get("assignee", {}), ASSIGNEE_RULES) if x.get("assignee") else None,
}


# ====================
# Normalize Functions
# ====================

def normalize_user(raw: Dict) -> Dict:
    """Normalize a user response."""
    if not raw:
        return {}
    # Handle nested user object from /user endpoint
    user_data = raw.get("user", raw)
    return normalize(user_data, USER_RULES)


def normalize_team(raw: Dict) -> Dict:
    """Normalize a single team/workspace."""
    return normalize(raw, TEAM_RULES)


def normalize_teams(raw: Dict) -> Dict:
    """Normalize teams list response."""
    if not raw:
        return {"workspaces": []}
    teams = raw.get("teams", [])
    return {
        "workspaces": [normalize_team(t) for t in teams]
    }


def normalize_members(raw: Dict) -> Dict:
    """Normalize team members response."""
    if not raw:
        return {"members": []}
    members = raw.get("members", [])
    return {
        "members": [normalize(m, MEMBER_RULES) for m in members]
    }


def normalize_space(raw: Dict) -> Dict:
    """Normalize a single space."""
    return normalize(raw, SPACE_RULES)


def normalize_spaces(raw: Dict) -> Dict:
    """Normalize spaces list response."""
    if not raw:
        return {"spaces": []}
    spaces = raw.get("spaces", [])
    return {
        "spaces": [normalize_space(s) for s in spaces]
    }


def normalize_folder(raw: Dict) -> Dict:
    """Normalize a single folder."""
    return normalize(raw, FOLDER_RULES)


def normalize_folders(raw: Dict) -> Dict:
    """Normalize folders list response."""
    if not raw:
        return {"folders": []}
    folders = raw.get("folders", [])
    return {
        "folders": [normalize_folder(f) for f in folders]
    }


def normalize_list(raw: Dict) -> Dict:
    """Normalize a single list."""
    return normalize(raw, LIST_RULES)


def normalize_lists(raw: Dict) -> Dict:
    """Normalize lists response."""
    if not raw:
        return {"lists": []}
    lists = raw.get("lists", [])
    return {
        "lists": [normalize_list(lst) for lst in lists]
    }


def normalize_task(raw: Dict) -> Dict:
    """Normalize a single task."""
    return normalize(raw, TASK_RULES)


def normalize_tasks(raw: Dict) -> Dict:
    """Normalize tasks list response."""
    if not raw:
        return {"tasks": []}
    tasks = raw.get("tasks", [])
    return {
        "tasks": [normalize_task(t) for t in tasks]
    }


def normalize_comment(raw: Dict) -> Dict:
    """Normalize a single comment."""
    return normalize(raw, COMMENT_RULES)


def normalize_comments(raw: Dict) -> Dict:
    """Normalize comments list response."""
    if not raw:
        return {"comments": []}
    comments = raw.get("comments", [])
    return {
        "comments": [normalize_comment(c) for c in comments]
    }

