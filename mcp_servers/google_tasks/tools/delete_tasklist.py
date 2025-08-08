from __future__ import annotations

import logging

from googleapiclient.errors import HttpError

from . import get_service

logger = logging.getLogger(__name__)


def delete_tasklist(tasklist_id: str) -> None:
    service = get_service()
    try:
        service.tasklists().delete(tasklist=tasklist_id).execute(num_retries=3)
    except HttpError as exc:
        logger.exception("Google Tasks API error while deleting tasklist %s: %s", tasklist_id, exc)
        raise

