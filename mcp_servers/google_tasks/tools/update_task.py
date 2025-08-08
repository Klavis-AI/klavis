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


def update_task(
    tasklist_id: str,
    task_id: str,
    **updates: Any,
) -> Dict[str, Any]:
    service = get_service()
    try:
        existing = service.tasks().get(tasklist=tasklist_id, task=task_id).execute()
        existing.update(updates)
        return (
            service.tasks()
            .update(tasklist=tasklist_id, task=task_id, body=existing)
            .execute(num_retries=3)
        )
    except HttpError as exc:
        logger.exception("Google Tasks API error while updating task %s: %s", task_id, exc)
        raise

