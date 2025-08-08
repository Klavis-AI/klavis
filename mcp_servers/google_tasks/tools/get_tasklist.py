from __future__ import annotations

import logging
from typing import Any, Dict

from googleapiclient.errors import HttpError

from . import get_service

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

