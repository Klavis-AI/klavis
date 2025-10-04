from __future__ import annotations

import logging

from googleapiclient.errors import HttpError

try:  # package context
    from ..auth import get_service  # type: ignore
except Exception:
    try:  # script context
        from auth import get_service  # type: ignore
    except Exception:  # repo-root context
        from mcp_servers.google_tasks.auth import get_service  # type: ignore

logger = logging.getLogger(__name__)


def delete_task(tasklist_id: str, task_id: str) -> None:
    service = get_service()
    try:
        service.tasks().delete(tasklist=tasklist_id, task=task_id).execute(num_retries=3)
    except HttpError as exc:
        logger.exception("Google Tasks API error while deleting task %s: %s", task_id, exc)
        raise

