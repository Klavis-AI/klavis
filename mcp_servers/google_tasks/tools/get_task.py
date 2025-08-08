from __future__ import annotations

import logging
from typing import Any, Dict

from googleapiclient.errors import HttpError

from . import get_service

logger = logging.getLogger(__name__)


def get_task(tasklist_id: str, task_id: str) -> Dict[str, Any]:
    service = get_service()
    try:
        return (
            service.tasks()
            .get(tasklist=tasklist_id, task=task_id)
            .execute(num_retries=3)
        )
    except HttpError as exc:
        logger.exception("Google Tasks API error while getting task %s: %s", task_id, exc)
        raise

