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


def update_tasklist(tasklist_id: str, title: str | None = None) -> Dict[str, Any]:
    """Update the given tasklist with full update semantics.

    Google update typically expects the full resource representation. We include
    fields we support and rely on the API to keep the rest unchanged.
    """
    service = get_service()
    body: Dict[str, Any] = {"id": tasklist_id}
    if title is not None:
        body["title"] = title
    try:
        return (
            service.tasklists()
            .update(tasklist=tasklist_id, body=body)
            .execute(num_retries=3)
        )
    except HttpError as exc:
        logger.exception("Google Tasks API error while updating tasklist %s: %s", tasklist_id, exc)
        raise

