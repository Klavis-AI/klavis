"""
Domain package for Zapier MCP Server.

This module contains the core business entities, value objects,
and domain logic that represent the business concepts.
"""

from .entities import Workflow, Task, Webhook, App
from .value_objects import WorkflowStatus, TaskStatus, WebhookEvent
from .exceptions import DomainError, WorkflowNotFoundError, InvalidWorkflowStateError

__all__ = [
    # Entities
    "Workflow",
    "Task", 
    "Webhook",
    "App",
    
    # Value Objects
    "WorkflowStatus",
    "TaskStatus", 
    "WebhookEvent",
    
    # Domain Exceptions
    "DomainError",
    "WorkflowNotFoundError",
    "InvalidWorkflowStateError"
] 