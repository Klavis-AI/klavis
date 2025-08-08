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


def get_tasklist(tasklist_id: str) -> Dict[str, Any]:
    service = get_service()
    try:
        return (
            service.tasklists()
            .get(tasklist=tasklist_id)
            .execute(num_retries=3)
        )
    except HttpError as exc:
        logger.exception("Google Tasks API error while getting tasklist %s: %s", tasklist_id, exc)
        raise

