from __future__ import annotations

import contextvars

# Support running both as a package (python -m mcp_servers.google_tasks.server)
# and as a script (python mcp_servers/google_tasks/server.py)
try:  # package context
    from ..auth import get_tasks_service  # type: ignore
except Exception:
    try:  # script context (auth.py is alongside this package directory)
        from auth import get_tasks_service  # type: ignore
    except Exception:  # repo-root context
        from mcp_servers.google_tasks.auth import get_tasks_service  # type: ignore

from .clear_completed_tasks import clear_completed_tasks
from .create_task import create_task
from .create_tasklist import create_tasklist
from .delete_task import delete_task
from .delete_tasklist import delete_tasklist
from .get_task import get_task
from .get_tasklist import get_tasklist
from .list_tasks import list_tasks
from .list_tasklists import list_tasklists
from .move_task import move_task
from .patch_task import patch_task
from .patch_tasklist import patch_tasklist
from .update_task import update_task
from .update_tasklist import update_tasklist

__all__ = [
    "tasks_service_context",
    "clear_completed_tasks",
    "create_task",
    "create_tasklist",
    "delete_task",
    "delete_tasklist",
    "get_task",
    "get_tasklist",
    "list_tasks",
    "list_tasklists",
    "move_task",
    "patch_task",
    "patch_tasklist",
    "update_task",
    "update_tasklist",
]

# Context variable to allow per-request override if needed.
# We lazily create the Google Tasks service on first access after environment
# variables are guaranteed to be loaded.

tasks_service_context: contextvars.ContextVar = contextvars.ContextVar(
    "google_tasks_service", default=None
)

def get_service():
    svc = tasks_service_context.get()
    if svc is None:
        svc = get_tasks_service()
        tasks_service_context.set(svc)
    return svc
