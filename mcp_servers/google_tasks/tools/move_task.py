from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from googleapiclient.errors import HttpError

try:  # package context
    from ..auth import get_service  # type: ignore
except Exception:
    try:  # script context
        from auth import get_service  # type: ignore
    except Exception:  # repo-root context
        from mcp_servers.google_tasks.auth import get_service  # type: ignore

logger = logging.getLogger(__name__)


def move_task(
    tasklist_id: str,
    task_id: str,
    parent: Optional[str] = None,
    previous: Optional[str] = None,
) -> Dict[str, Any]:
    service = get_service()
    try:
        return (
            service.tasks()
            .move(tasklist=tasklist_id, task=task_id, parent=parent, previous=previous)
            .execute(num_retries=3)
        )
    except HttpError as exc:
        logger.exception("Google Tasks API error while moving task %s: %s", task_id, exc)
        raise

