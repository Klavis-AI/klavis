from __future__ import annotations

import logging
from typing import Any, Dict, List

from googleapiclient.errors import HttpError

try:  # package context
    from ..auth import get_service  # type: ignore
except Exception:
    try:  # script context
        from auth import get_service  # type: ignore
    except Exception:  # repo-root context
        from mcp_servers.google_tasks.auth import get_service  # type: ignore

logger = logging.getLogger(__name__)


def list_tasks(tasklist_id: str, show_completed: bool = True, max_results: int | None = 100) -> List[Dict[str, Any]]:
    service = get_service()
    try:
        response = (
            service.tasks()
            .list(tasklist=tasklist_id, showCompleted=show_completed, maxResults=max_results)
            .execute(num_retries=3)
        )
        return response.get("items", [])
    except HttpError as exc:
        logger.exception("Google Tasks API error while listing tasks: %s", exc)
        raise

