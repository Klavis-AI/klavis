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


def list_tasklists(max_results: int | None = 100) -> List[Dict[str, Any]]:
    """List the user's tasklists.

    Parameters
    ----------
    max_results: int | None
        Maximum number of tasklists to return (Google default 20, max 100).

    Returns
    -------
    list[dict]
        Each item is the raw JSON object returned by Google Tasks API.
    """
    service = get_service()
    try:
        response = (
            service.tasklists()
            .list(maxResults=max_results)
            .execute(num_retries=3)
        )
        return response.get("items", [])
    except HttpError as exc:
        logger.exception("Google Tasks API error while listing tasklists: %s", exc)
        raise

