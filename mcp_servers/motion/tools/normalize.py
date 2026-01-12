from typing import Any, Dict, List

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


# Mapping Rules

USER_RULES = {
    "id": "id",
    "name": "name",
    "email": "email",
}

WORKSPACE_RULES = {
    "id": "id",
    "name": "name",
    "teamId": "teamId",
    "type": "type",
}

PROJECT_RULES = {
    "id": "id",
    "name": "name",
    "description": "description",
    "workspaceId": "workspaceId",
    "status": lambda x: x.get("status", {}).get("name") if isinstance(x.get("status"), dict) else x.get("status"),
}

ASSIGNEE_RULES = {
    "id": "id",
    "name": "name",
    "email": "email",
}

LABEL_RULES = {
    "name": "name",
}

TASK_RULES = {
    "id": "id",
    "name": "name",
    "description": "description",
    "status": lambda x: x.get("status", {}).get("name") if isinstance(x.get("status"), dict) else x.get("status"),
    "priority": "priority",
    "dueDate": "dueDate",
    "scheduledStart": "scheduledStart",
    "scheduledEnd": "scheduledEnd",
    "duration": "duration",
    "completed": "completed",
    "createdAt": "createdAt",
    "workspaceId": "workspace.id",
    "workspaceName": "workspace.name",
    "projectId": "project.id",
    "projectName": "project.name",
    # Nested objects
    "assignees": lambda x: [
        normalize(a, ASSIGNEE_RULES) for a in x.get("assignees", [])
    ] if x.get("assignees") else None,
    "labels": lambda x: [
        normalize(l, LABEL_RULES) for l in x.get("labels", [])
    ] if x.get("labels") else None,
}

COMMENT_CREATOR_RULES = {
    "id": "id",
    "name": "name",
}

COMMENT_RULES = {
    "id": "id",
    "taskId": "taskId",
    "content": "content",
    "createdAt": "createdAt",
    "creatorId": "creator.id",
    "creatorName": "creator.name",
}


def normalize_task(raw_task: Dict) -> Dict:
    """Normalize a single task."""
    return normalize(raw_task, TASK_RULES)


def normalize_tasks(raw_tasks: List[Dict]) -> List[Dict]:
    """Normalize a list of tasks."""
    return [normalize_task(t) for t in raw_tasks]


def normalize_project(raw_project: Dict) -> Dict:
    """Normalize a single project."""
    return normalize(raw_project, PROJECT_RULES)


def normalize_projects(raw_projects: List[Dict]) -> List[Dict]:
    """Normalize a list of projects."""
    return [normalize_project(p) for p in raw_projects]


def normalize_user(raw_user: Dict) -> Dict:
    """Normalize a single user."""
    return normalize(raw_user, USER_RULES)


def normalize_users(raw_users: List[Dict]) -> List[Dict]:
    """Normalize a list of users."""
    return [normalize_user(u) for u in raw_users]


def normalize_workspace(raw_workspace: Dict) -> Dict:
    """Normalize a single workspace."""
    return normalize(raw_workspace, WORKSPACE_RULES)


def normalize_workspaces(raw_workspaces: List[Dict]) -> List[Dict]:
    """Normalize a list of workspaces."""
    return [normalize_workspace(w) for w in raw_workspaces]


def normalize_comment(raw_comment: Dict) -> Dict:
    """Normalize a single comment."""
    return normalize(raw_comment, COMMENT_RULES)


def normalize_comments(raw_comments: List[Dict]) -> List[Dict]:
    """Normalize a list of comments."""
    return [normalize_comment(c) for c in raw_comments]

