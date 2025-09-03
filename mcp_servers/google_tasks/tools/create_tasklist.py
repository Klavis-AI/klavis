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


def create_tasklist(title: str) -> Dict[str, Any]:
    service = get_service()
    body = {"title": title}
    try:
        return (
            service.tasklists()
            .insert(body=body)
            .execute(num_retries=3)
        )
    except HttpError as exc:
        logger.exception("Google Tasks API error while creating tasklist: %s", exc)
        raise

