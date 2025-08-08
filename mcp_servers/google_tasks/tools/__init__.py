from __future__ import annotations

import contextvars

from ..auth import get_tasks_service

__all__ = [
    "tasks_service_context",
]

# Context variable to allow per-request override if needed (future-proofing)
# but by default will hold the shared service instance.
_tasks_service = get_tasks_service()

tasks_service_context: contextvars.ContextVar = contextvars.ContextVar(
    "google_tasks_service", default=_tasks_service
)

