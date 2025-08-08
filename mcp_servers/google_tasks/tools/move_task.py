from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from googleapiclient.errors import HttpError

from . import get_service

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

