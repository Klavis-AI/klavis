from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from googleapiclient.errors import HttpError

from . import tasks_service_context

logger = logging.getLogger(__name__)


def list_tasks(tasklist_id: str, show_completed: bool = True, max_results: int | None = 100) -> List[Dict[str, Any]]:
    service = tasks_service_context.get()
    try:
        response = (
            service.tasks()
            .list(tasklist=tasklist_id, showCompleted=show_completed, maxResults=max_results)
            .execute(num_retries=3)
        )
        return response.get("items", [])
    except HttpError as exc:
        logger.exception("Google Tasks API error while listing tasks: %s", exc)
        raise


def get_task(tasklist_id: str, task_id: str) -> Dict[str, Any]:
    service = tasks_service_context.get()
    try:
        return (
            service.tasks()
            .get(tasklist=tasklist_id, task=task_id)
            .execute(num_retries=3)
        )
    except HttpError as exc:
        logger.exception("Google Tasks API error while getting task %s: %s", task_id, exc)
        raise


def create_task(
    tasklist_id: str,
    title: str,
    notes: Optional[str] = None,
    due: Optional[str] = None,
    parent: Optional[str] = None,
    position: Optional[str] = None,
) -> Dict[str, Any]:
    service = tasks_service_context.get()
    body: Dict[str, Any] = {"title": title}
    if notes is not None:
        body["notes"] = notes
    if due is not None:
        body["due"] = due
    if parent is not None:
        body["parent"] = parent
    if position is not None:
        body["position"] = position

    try:
        return (
            service.tasks()
            .insert(tasklist=tasklist_id, body=body)
            .execute(num_retries=3)
        )
    except HttpError as exc:
        logger.exception("Google Tasks API error while creating task: %s", exc)
        raise


def update_task(
    tasklist_id: str,
    task_id: str,
    **updates: Any,
) -> Dict[str, Any]:
    service = tasks_service_context.get()
    try:
        existing = service.tasks().get(tasklist=tasklist_id, task=task_id).execute()
        existing.update(updates)
        return (
            service.tasks()
            .update(tasklist=tasklist_id, task=task_id, body=existing)
            .execute(num_retries=3)
        )
    except HttpError as exc:
        logger.exception("Google Tasks API error while updating task %s: %s", task_id, exc)
        raise


def move_task(
    tasklist_id: str,
    task_id: str,
    parent: Optional[str] = None,
    previous: Optional[str] = None,
) -> Dict[str, Any]:
    service = tasks_service_context.get()
    try:
        return (
            service.tasks()
            .move(tasklist=tasklist_id, task=task_id, parent=parent, previous=previous)
            .execute(num_retries=3)
        )
    except HttpError as exc:
        logger.exception("Google Tasks API error while moving task %s: %s", task_id, exc)
        raise


def clear_completed_tasks(tasklist_id: str) -> None:
    service = tasks_service_context.get()
    try:
        service.tasks().clear(tasklist=tasklist_id).execute(num_retries=3)
    except HttpError as exc:
        logger.exception("Google Tasks API error while clearing completed tasks in tasklist %s: %s", tasklist_id, exc)
        raise


def delete_task(tasklist_id: str, task_id: str) -> None:
    service = tasks_service_context.get()
    try:
        service.tasks().delete(tasklist=tasklist_id, task=task_id).execute(num_retries=3)
    except HttpError as exc:
        logger.exception("Google Tasks API error while deleting task %s: %s", task_id, exc)
        raise

