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


def patch_tasklist(tasklist_id: str, **fields: Any) -> Dict[str, Any]:
    """Patch the given tasklist.

    Only the provided fields will be updated. Common fields include:
    - title: str
    """
    service = get_service()
    try:
        return (
            service.tasklists()
            .patch(tasklist=tasklist_id, body=fields)
            .execute(num_retries=3)
        )
    except HttpError as exc:
        logger.exception("Google Tasks API error while patching tasklist %s: %s", tasklist_id, exc)
        raise

