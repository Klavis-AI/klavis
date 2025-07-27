"""
Domain entities for Zapier MCP Server.

This module contains the core business entities that represent
the main concepts in the Zapier domain.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, computed_field
from enum import Enum

from .value_objects import WorkflowStatus, TaskStatus, WebhookEvent


class Workflow(BaseModel):
    """
    Workflow entity representing a Zapier workflow.
    
    This is the core business entity that represents an automation
    workflow in Zapier.
    """
    
    id: str = Field(..., description="Unique workflow identifier")
    title: str = Field(..., min_length=1, max_length=200, description="Workflow title")
    description: Optional[str] = Field(None, max_length=1000, description="Workflow description")
    status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT, description="Workflow status")
    
    # Trigger configuration
    trigger_app: Optional[str] = Field(None, description="Trigger app name")
    trigger_event: Optional[str] = Field(None, description="Trigger event name")
    trigger_config: Dict[str, Any] = Field(default_factory=dict, description="Trigger configuration")
    
    # Action configuration
    action_app: Optional[str] = Field(None, description="Action app name")
    action_event: Optional[str] = Field(None, description="Action event name")
    action_config: Dict[str, Any] = Field(default_factory=dict, description="Action configuration")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    
    # Statistics
    execution_count: int = Field(default=0, description="Number of executions")
    last_executed_at: Optional[datetime] = Field(None, description="Last execution timestamp")
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Success rate (0-1)")
    
    @computed_field
    @property
    def is_active(self) -> bool:
        """Check if workflow is active."""
        return self.status == WorkflowStatus.ACTIVE
    
    @computed_field
    @property
    def is_draft(self) -> bool:
        """Check if workflow is in draft status."""
        return self.status == WorkflowStatus.DRAFT
    
    @computed_field
    @property
    def is_complete(self) -> bool:
        """Check if workflow is complete."""
        return self.status == WorkflowStatus.COMPLETED
    
    @computed_field
    @property
    def has_trigger(self) -> bool:
        """Check if workflow has a trigger configured."""
        return bool(self.trigger_app and self.trigger_event)
    
    @computed_field
    @property
    def has_action(self) -> bool:
        """Check if workflow has an action configured."""
        return bool(self.action_app and self.action_event)
    
    @computed_field
    @property
    def is_ready(self) -> bool:
        """Check if workflow is ready for execution."""
        return self.is_active and self.has_trigger and self.has_action
    
    def activate(self) -> None:
        """Activate the workflow."""
        if not self.has_trigger or not self.has_action:
            raise ValueError("Workflow must have both trigger and action to be activated")
        self.status = WorkflowStatus.ACTIVE
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate the workflow."""
        self.status = WorkflowStatus.DRAFT
        self.updated_at = datetime.utcnow()
    
    def execute(self, success: bool = True) -> None:
        """Record workflow execution."""
        self.execution_count += 1
        self.last_executed_at = datetime.utcnow()
        
        # Update success rate
        if self.execution_count == 1:
            self.success_rate = 1.0 if success else 0.0
        else:
            # Simple moving average
            current_success = 1.0 if success else 0.0
            self.success_rate = (self.success_rate * (self.execution_count - 1) + current_success) / self.execution_count
        
        self.updated_at = datetime.utcnow()


class Task(BaseModel):
    """
    Task entity representing a workflow execution task.
    
    This entity represents a single execution of a workflow,
    including its status and results.
    """
    
    id: str = Field(..., description="Unique task identifier")
    workflow_id: str = Field(..., description="Associated workflow ID")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task status")
    
    # Execution details
    started_at: Optional[datetime] = Field(None, description="Execution start time")
    completed_at: Optional[datetime] = Field(None, description="Execution completion time")
    duration_seconds: Optional[float] = Field(None, description="Execution duration in seconds")
    
    # Input/Output data
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data for the task")
    output_data: Dict[str, Any] = Field(default_factory=dict, description="Output data from the task")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    @computed_field
    @property
    def is_pending(self) -> bool:
        """Check if task is pending."""
        return self.status == TaskStatus.PENDING
    
    @computed_field
    @property
    def is_running(self) -> bool:
        """Check if task is running."""
        return self.status == TaskStatus.RUNNING
    
    @computed_field
    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status == TaskStatus.COMPLETED
    
    @computed_field
    @property
    def is_failed(self) -> bool:
        """Check if task failed."""
        return self.status == TaskStatus.FAILED
    
    @computed_field
    @property
    def is_cancelled(self) -> bool:
        """Check if task was cancelled."""
        return self.status == TaskStatus.CANCELLED
    
    def start(self) -> None:
        """Start the task execution."""
        if self.status != TaskStatus.PENDING:
            raise ValueError(f"Cannot start task in {self.status} status")
        
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def complete(self, output_data: Optional[Dict[str, Any]] = None) -> None:
        """Complete the task successfully."""
        if self.status != TaskStatus.RUNNING:
            raise ValueError(f"Cannot complete task in {self.status} status")
        
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        
        if output_data:
            self.output_data = output_data
        
        self.updated_at = datetime.utcnow()
    
    def fail(self, error_message: str) -> None:
        """Mark the task as failed."""
        if self.status != TaskStatus.RUNNING:
            raise ValueError(f"Cannot fail task in {self.status} status")
        
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        self.error_message = error_message
        
        self.updated_at = datetime.utcnow()
    
    def cancel(self) -> None:
        """Cancel the task."""
        if self.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            raise ValueError(f"Cannot cancel task in {self.status} status")
        
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        
        self.updated_at = datetime.utcnow()


class Webhook(BaseModel):
    """
    Webhook entity representing a webhook endpoint.
    
    This entity represents a webhook that can trigger workflows
    or receive data from external systems.
    """
    
    id: str = Field(..., description="Unique webhook identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Webhook name")
    url: str = Field(..., description="Webhook URL")
    secret: Optional[str] = Field(None, description="Webhook secret for verification")
    
    # Configuration
    events: List[WebhookEvent] = Field(default_factory=list, description="Supported events")
    is_active: bool = Field(default=True, description="Whether webhook is active")
    retry_count: int = Field(default=3, ge=0, le=10, description="Number of retry attempts")
    timeout_seconds: int = Field(default=30, ge=1, le=300, description="Request timeout")
    
    # Statistics
    call_count: int = Field(default=0, description="Number of webhook calls")
    success_count: int = Field(default=0, description="Number of successful calls")
    last_called_at: Optional[datetime] = Field(None, description="Last call timestamp")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    
    @computed_field
    @property
    def failure_count(self) -> int:
        """Calculate number of failed calls."""
        return self.call_count - self.success_count
    
    @computed_field
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.call_count == 0:
            return 0.0
        return self.success_count / self.call_count
    
    def call(self, success: bool = True) -> None:
        """Record a webhook call."""
        self.call_count += 1
        if success:
            self.success_count += 1
        self.last_called_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate the webhook."""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate the webhook."""
        self.is_active = False
        self.updated_at = datetime.utcnow()


class App(BaseModel):
    """
    App entity representing a connected application.
    
    This entity represents an application that is connected
    to Zapier and can be used in workflows.
    """
    
    id: str = Field(..., description="Unique app identifier")
    name: str = Field(..., min_length=1, max_length=100, description="App name")
    description: Optional[str] = Field(None, max_length=500, description="App description")
    
    # Connection details
    api_key: Optional[str] = Field(None, description="API key for the app")
    is_connected: bool = Field(default=False, description="Whether app is connected")
    connection_status: str = Field(default="disconnected", description="Connection status")
    
    # Capabilities
    supported_triggers: List[str] = Field(default_factory=list, description="Supported trigger events")
    supported_actions: List[str] = Field(default_factory=list, description="Supported action events")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    last_sync_at: Optional[datetime] = Field(None, description="Last sync timestamp")
    
    @computed_field
    @property
    def has_triggers(self) -> bool:
        """Check if app has trigger capabilities."""
        return len(self.supported_triggers) > 0
    
    @computed_field
    @property
    def has_actions(self) -> bool:
        """Check if app has action capabilities."""
        return len(self.supported_actions) > 0
    
    @computed_field
    @property
    def is_fully_connected(self) -> bool:
        """Check if app is fully connected and ready."""
        return self.is_connected and self.connection_status == "connected"
    
    def connect(self, api_key: str) -> None:
        """Connect the app with API key."""
        self.api_key = api_key
        self.is_connected = True
        self.connection_status = "connected"
        self.updated_at = datetime.utcnow()
    
    def disconnect(self) -> None:
        """Disconnect the app."""
        self.api_key = None
        self.is_connected = False
        self.connection_status = "disconnected"
        self.updated_at = datetime.utcnow()
    
    def sync(self) -> None:
        """Sync app capabilities."""
        if not self.is_connected:
            raise ValueError("Cannot sync disconnected app")
        
        self.last_sync_at = datetime.utcnow()
        self.updated_at = datetime.utcnow() 