from __future__ import annotations

import logging

from googleapiclient.errors import HttpError

from . import get_service

logger = logging.getLogger(__name__)


def clear_completed_tasks(tasklist_id: str) -> None:
    service = get_service()
    try:
        service.tasks().clear(tasklist=tasklist_id).execute(num_retries=3)
    except HttpError as exc:
        logger.exception("Google Tasks API error while clearing completed tasks in tasklist %s: %s", tasklist_id, exc)
        raise

