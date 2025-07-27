"""
Value objects for Zapier MCP Server.

This module contains value objects that represent immutable
values in the domain model.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    """Workflow status enumeration."""
    
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    ERROR = "error"


class TaskStatus(str, Enum):
    """Task status enumeration."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class WebhookEvent(str, Enum):
    """Webhook event types."""
    
    WORKFLOW_TRIGGERED = "workflow.triggered"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    APP_CONNECTED = "app.connected"
    APP_DISCONNECTED = "app.disconnected"


class WorkflowId(BaseModel):
    """Value object for workflow ID."""
    
    value: str = Field(..., min_length=1, max_length=50)
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"WorkflowId({self.value})"


class TaskId(BaseModel):
    """Value object for task ID."""
    
    value: str = Field(..., min_length=1, max_length=50)
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"TaskId({self.value})"


class WebhookId(BaseModel):
    """Value object for webhook ID."""
    
    value: str = Field(..., min_length=1, max_length=50)
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"WebhookId({self.value})"


class AppId(BaseModel):
    """Value object for app ID."""
    
    value: str = Field(..., min_length=1, max_length=50)
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"AppId({self.value})"


class ApiKey(BaseModel):
    """Value object for API key."""
    
    value: str = Field(..., min_length=1, max_length=100)
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"ApiKey({self.value[:8]}...)"  # Only show first 8 chars for security


class WebhookUrl(BaseModel):
    """Value object for webhook URL."""
    
    value: str = Field(..., min_length=1, max_length=500)
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"WebhookUrl({self.value})"


class WorkflowTitle(BaseModel):
    """Value object for workflow title."""
    
    value: str = Field(..., min_length=1, max_length=200)
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"WorkflowTitle({self.value})"


class WorkflowDescription(BaseModel):
    """Value object for workflow description."""
    
    value: Optional[str] = Field(None, max_length=1000)
    
    def __str__(self) -> str:
        return self.value or ""
    
    def __repr__(self) -> str:
        return f"WorkflowDescription({self.value})"


class ExecutionCount(BaseModel):
    """Value object for execution count."""
    
    value: int = Field(..., ge=0)
    
    def __str__(self) -> str:
        return str(self.value)
    
    def __repr__(self) -> str:
        return f"ExecutionCount({self.value})"
    
    def increment(self) -> "ExecutionCount":
        """Increment the execution count."""
        return ExecutionCount(value=self.value + 1)


class SuccessRate(BaseModel):
    """Value object for success rate."""
    
    value: float = Field(..., ge=0.0, le=1.0)
    
    def __str__(self) -> str:
        return f"{self.value:.2%}"
    
    def __repr__(self) -> str:
        return f"SuccessRate({self.value:.2%})"
    
    def update(self, success: bool, total_count: int) -> "SuccessRate":
        """Update success rate with new execution result."""
        if total_count == 0:
            return SuccessRate(value=1.0 if success else 0.0)
        
        current_success = 1.0 if success else 0.0
        new_rate = (self.value * (total_count - 1) + current_success) / total_count
        return SuccessRate(value=new_rate)


class Duration(BaseModel):
    """Value object for duration in seconds."""
    
    value: float = Field(..., ge=0.0)
    
    def __str__(self) -> str:
        if self.value < 60:
            return f"{self.value:.2f}s"
        elif self.value < 3600:
            minutes = self.value / 60
            return f"{minutes:.1f}m"
        else:
            hours = self.value / 3600
            return f"{hours:.1f}h"
    
    def __repr__(self) -> str:
        return f"Duration({self.value}s)"


class RetryCount(BaseModel):
    """Value object for retry count."""
    
    value: int = Field(..., ge=0, le=10)
    
    def __str__(self) -> str:
        return str(self.value)
    
    def __repr__(self) -> str:
        return f"RetryCount({self.value})"
    
    def increment(self) -> "RetryCount":
        """Increment the retry count."""
        if self.value >= 10:
            raise ValueError("Maximum retry count reached")
        return RetryCount(value=self.value + 1)


class Timeout(BaseModel):
    """Value object for timeout in seconds."""
    
    value: int = Field(..., ge=1, le=300)
    
    def __str__(self) -> str:
        return f"{self.value}s"
    
    def __repr__(self) -> str:
        return f"Timeout({self.value}s)"


class Pagination(BaseModel):
    """Value object for pagination parameters."""
    
    limit: int = Field(..., ge=1, le=100)
    offset: int = Field(..., ge=0)
    sort_by: Optional[str] = Field(None)
    sort_order: Optional[str] = Field(None, regex="^(asc|desc)$")
    
    def __str__(self) -> str:
        return f"Pagination(limit={self.limit}, offset={self.offset})"
    
    def __repr__(self) -> str:
        return f"Pagination(limit={self.limit}, offset={self.offset}, sort_by={self.sort_by}, sort_order={self.sort_order})"
    
    def next_page(self) -> "Pagination":
        """Get next page pagination."""
        return Pagination(
            limit=self.limit,
            offset=self.offset + self.limit,
            sort_by=self.sort_by,
            sort_order=self.sort_order
        )
    
    def previous_page(self) -> "Pagination":
        """Get previous page pagination."""
        new_offset = max(0, self.offset - self.limit)
        return Pagination(
            limit=self.limit,
            offset=new_offset,
            sort_by=self.sort_by,
            sort_order=self.sort_order
        ) 