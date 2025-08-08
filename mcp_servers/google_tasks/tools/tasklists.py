from __future__ import annotations

import logging
from typing import Any, Dict, List

from googleapiclient.errors import HttpError

from . import tasks_service_context

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
    service = tasks_service_context.get()
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


def get_tasklist(tasklist_id: str) -> Dict[str, Any]:
    service = tasks_service_context.get()
    try:
        return (
            service.tasklists()
            .get(tasklist=tasklist_id)
            .execute(num_retries=3)
        )
    except HttpError as exc:
        logger.exception("Google Tasks API error while getting tasklist %s: %s", tasklist_id, exc)
        raise


def create_tasklist(title: str) -> Dict[str, Any]:
    service = tasks_service_context.get()
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


def delete_tasklist(tasklist_id: str) -> None:
    service = tasks_service_context.get()
    try:
        service.tasklists().delete(tasklist=tasklist_id).execute(num_retries=3)
    except HttpError as exc:
        logger.exception("Google Tasks API error while deleting tasklist %s: %s", tasklist_id, exc)
        raise

