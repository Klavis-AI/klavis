from __future__ import annotations

import logging
from typing import Any, Dict

from googleapiclient.errors import HttpError

from . import get_service

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

