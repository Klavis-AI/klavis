"""
Domain exceptions for Zapier MCP Server.

This module contains domain-specific exceptions that represent
business rule violations and domain errors.
"""

from typing import Optional, Any, Dict
from .value_objects import WorkflowId, TaskId, WebhookId, AppId


class DomainError(Exception):
    """
    Base exception for all domain errors.
    
    This is the base exception for all domain-specific errors
    that represent business rule violations.
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize domain error."""
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format."""
        return {
            "error": self.message,
            "error_type": self.__class__.__name__,
            "details": self.details
        }


class WorkflowNotFoundError(DomainError):
    """
    Exception raised when a workflow is not found.
    
    This exception is raised when attempting to access a workflow
    that doesn't exist in the system.
    """
    
    def __init__(self, workflow_id: WorkflowId, message: Optional[str] = None):
        """Initialize workflow not found error."""
        if message is None:
            message = f"Workflow with ID '{workflow_id}' not found"
        
        super().__init__(message, {"workflow_id": str(workflow_id)})
        self.workflow_id = workflow_id


class InvalidWorkflowStateError(DomainError):
    """
    Exception raised when workflow state transition is invalid.
    
    This exception is raised when attempting to perform an operation
    on a workflow that is not in the correct state.
    """
    
    def __init__(
        self,
        workflow_id: WorkflowId,
        current_state: str,
        required_state: str,
        operation: str,
        message: Optional[str] = None
    ):
        """Initialize invalid workflow state error."""
        if message is None:
            message = f"Cannot perform '{operation}' on workflow '{workflow_id}' in state '{current_state}'. Required state: '{required_state}'"
        
        super().__init__(message, {
            "workflow_id": str(workflow_id),
            "current_state": current_state,
            "required_state": required_state,
            "operation": operation
        })
        self.workflow_id = workflow_id
        self.current_state = current_state
        self.required_state = required_state
        self.operation = operation


class WorkflowValidationError(DomainError):
    """
    Exception raised when workflow validation fails.
    
    This exception is raised when workflow data doesn't meet
    business validation rules.
    """
    
    def __init__(self, field: str, value: Any, rule: str, message: Optional[str] = None):
        """Initialize workflow validation error."""
        if message is None:
            message = f"Validation failed for field '{field}' with value '{value}'. Rule: {rule}"
        
        super().__init__(message, {
            "field": field,
            "value": value,
            "rule": rule
        })
        self.field = field
        self.value = value
        self.rule = rule


class TaskNotFoundError(DomainError):
    """
    Exception raised when a task is not found.
    
    This exception is raised when attempting to access a task
    that doesn't exist in the system.
    """
    
    def __init__(self, task_id: TaskId, message: Optional[str] = None):
        """Initialize task not found error."""
        if message is None:
            message = f"Task with ID '{task_id}' not found"
        
        super().__init__(message, {"task_id": str(task_id)})
        self.task_id = task_id


class InvalidTaskStateError(DomainError):
    """
    Exception raised when task state transition is invalid.
    
    This exception is raised when attempting to perform an operation
    on a task that is not in the correct state.
    """
    
    def __init__(
        self,
        task_id: TaskId,
        current_state: str,
        required_state: str,
        operation: str,
        message: Optional[str] = None
    ):
        """Initialize invalid task state error."""
        if message is None:
            message = f"Cannot perform '{operation}' on task '{task_id}' in state '{current_state}'. Required state: '{required_state}'"
        
        super().__init__(message, {
            "task_id": str(task_id),
            "current_state": current_state,
            "required_state": required_state,
            "operation": operation
        })
        self.task_id = task_id
        self.current_state = current_state
        self.required_state = required_state
        self.operation = operation


class WebhookNotFoundError(DomainError):
    """
    Exception raised when a webhook is not found.
    
    This exception is raised when attempting to access a webhook
    that doesn't exist in the system.
    """
    
    def __init__(self, webhook_id: WebhookId, message: Optional[str] = None):
        """Initialize webhook not found error."""
        if message is None:
            message = f"Webhook with ID '{webhook_id}' not found"
        
        super().__init__(message, {"webhook_id": str(webhook_id)})
        self.webhook_id = webhook_id


class AppNotFoundError(DomainError):
    """
    Exception raised when an app is not found.
    
    This exception is raised when attempting to access an app
    that doesn't exist in the system.
    """
    
    def __init__(self, app_id: AppId, message: Optional[str] = None):
        """Initialize app not found error."""
        if message is None:
            message = f"App with ID '{app_id}' not found"
        
        super().__init__(message, {"app_id": str(app_id)})
        self.app_id = app_id


class AppConnectionError(DomainError):
    """
    Exception raised when app connection fails.
    
    This exception is raised when attempting to connect to an app
    that fails to authenticate or connect.
    """
    
    def __init__(self, app_id: AppId, reason: str, message: Optional[str] = None):
        """Initialize app connection error."""
        if message is None:
            message = f"Failed to connect to app '{app_id}'. Reason: {reason}"
        
        super().__init__(message, {
            "app_id": str(app_id),
            "reason": reason
        })
        self.app_id = app_id
        self.reason = reason


class WorkflowExecutionError(DomainError):
    """
    Exception raised when workflow execution fails.
    
    This exception is raised when a workflow execution fails
    due to business logic errors or external service failures.
    """
    
    def __init__(
        self,
        workflow_id: WorkflowId,
        task_id: Optional[TaskId] = None,
        error_code: Optional[str] = None,
        message: Optional[str] = None
    ):
        """Initialize workflow execution error."""
        if message is None:
            message = f"Workflow execution failed for workflow '{workflow_id}'"
            if task_id:
                message += f" in task '{task_id}'"
            if error_code:
                message += f". Error code: {error_code}"
        
        details = {
            "workflow_id": str(workflow_id),
            "error_code": error_code
        }
        if task_id:
            details["task_id"] = str(task_id)
        
        super().__init__(message, details)
        self.workflow_id = workflow_id
        self.task_id = task_id
        self.error_code = error_code


class WebhookDeliveryError(DomainError):
    """
    Exception raised when webhook delivery fails.
    
    This exception is raised when attempting to deliver a webhook
    that fails due to network issues or invalid configuration.
    """
    
    def __init__(
        self,
        webhook_id: WebhookId,
        url: str,
        status_code: Optional[int] = None,
        message: Optional[str] = None
    ):
        """Initialize webhook delivery error."""
        if message is None:
            message = f"Webhook delivery failed for webhook '{webhook_id}' to URL '{url}'"
            if status_code:
                message += f". Status code: {status_code}"
        
        super().__init__(message, {
            "webhook_id": str(webhook_id),
            "url": url,
            "status_code": status_code
        })
        self.webhook_id = webhook_id
        self.url = url
        self.status_code = status_code


class RateLimitExceededError(DomainError):
    """
    Exception raised when rate limits are exceeded.
    
    This exception is raised when API rate limits are exceeded
    for external services or internal operations.
    """
    
    def __init__(
        self,
        resource: str,
        limit: int,
        window_seconds: int,
        retry_after: Optional[int] = None,
        message: Optional[str] = None
    ):
        """Initialize rate limit exceeded error."""
        if message is None:
            message = f"Rate limit exceeded for resource '{resource}'. Limit: {limit} requests per {window_seconds} seconds"
            if retry_after:
                message += f". Retry after {retry_after} seconds"
        
        super().__init__(message, {
            "resource": resource,
            "limit": limit,
            "window_seconds": window_seconds,
            "retry_after": retry_after
        })
        self.resource = resource
        self.limit = limit
        self.window_seconds = window_seconds
        self.retry_after = retry_after


class ConfigurationError(DomainError):
    """
    Exception raised when configuration is invalid.
    
    This exception is raised when application configuration
    doesn't meet business requirements.
    """
    
    def __init__(self, setting: str, value: Any, reason: str, message: Optional[str] = None):
        """Initialize configuration error."""
        if message is None:
            message = f"Configuration error for setting '{setting}' with value '{value}'. Reason: {reason}"
        
        super().__init__(message, {
            "setting": setting,
            "value": value,
            "reason": reason
        })
        self.setting = setting
        self.value = value
        self.reason = reason 