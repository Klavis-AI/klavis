from __future__ import annotations

import logging

from googleapiclient.errors import HttpError

from . import get_service

logger = logging.getLogger(__name__)


def delete_task(tasklist_id: str, task_id: str) -> None:
    service = get_service()
    try:
        service.tasks().delete(tasklist=tasklist_id, task=task_id).execute(num_retries=3)
    except HttpError as exc:
        logger.exception("Google Tasks API error while deleting task %s: %s", task_id, exc)
        raise

