from __future__ import annotations

import logging
from typing import Any, Dict

from googleapiclient.errors import HttpError

try:  # package context
    from ..auth import get_service  # type: ignore
except Exception:
    try:  # script context
        from auth import get_service  # type: ignore
    except Exception:  # repo-root context
        from mcp_servers.google_tasks.auth import get_service  # type: ignore

logger = logging.getLogger(__name__)


def patch_task(
    tasklist_id: str,
    task_id: str,
    **fields: Any,
) -> Dict[str, Any]:
    """Patch the given task with partial fields (no read-modify-write)."""
    service = get_service()
    try:
        return (
            service.tasks()
            .patch(tasklist=tasklist_id, task=task_id, body=fields)
            .execute(num_retries=3)
        )
    except HttpError as exc:
        logger.exception("Google Tasks API error while patching task %s: %s", task_id, exc)
        raise

