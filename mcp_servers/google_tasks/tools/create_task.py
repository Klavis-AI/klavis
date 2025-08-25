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


def create_task(
    tasklist_id: str,
    title: str,
    notes: Optional[str] = None,
    due: Optional[str] = None,
    parent: Optional[str] = None,
    position: Optional[str] = None,
) -> Dict[str, Any]:
    service = get_service()
    body: Dict[str, Any] = {"title": title}
    if notes is not None:
        body["notes"] = notes
    if due is not None:
        body["due"] = due
    if parent is not None:
        body["parent"] = parent
    if position is not None:
        body["position"] = position

    try:
        return (
            service.tasks()
            .insert(tasklist=tasklist_id, body=body)
            .execute(num_retries=3)
        )
    except HttpError as exc:
        logger.exception("Google Tasks API error while creating task: %s", exc)
        raise

