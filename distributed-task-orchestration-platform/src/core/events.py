"""
Domain Events for Event-Driven Architecture.

Events are published when domain state changes.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from src.core.constants import TaskStatusEnum, WorkflowStatusEnum


@dataclass
class DomainEvent:
    """Base class for all domain events."""

    event_id: UUID
    timestamp: datetime
    aggregate_id: UUID
    aggregate_type: str
    event_type: str
    metadata: dict[str, Any] | None = None


# ========================================
# Workflow Events
# ========================================


@dataclass
class WorkflowCreated(DomainEvent):
    """Workflow was created."""

    workflow_name: str


@dataclass
class WorkflowStarted(DomainEvent):
    """Workflow execution started."""

    pass


@dataclass
class WorkflowCompleted(DomainEvent):
    """Workflow completed successfully."""

    duration_seconds: float


@dataclass
class WorkflowFailed(DomainEvent):
    """Workflow failed."""

    error_message: str


@dataclass
class WorkflowPaused(DomainEvent):
    """Workflow was paused."""

    pass


@dataclass
class WorkflowResumed(DomainEvent):
    """Workflow was resumed."""

    pass


@dataclass
class WorkflowCancelled(DomainEvent):
    """Workflow was cancelled."""

    pass


@dataclass
class WorkflowStatusChanged(DomainEvent):
    """Workflow status changed."""

    old_status: WorkflowStatusEnum
    new_status: WorkflowStatusEnum


# ========================================
# Task Events
# ========================================


@dataclass
class TaskCreated(DomainEvent):
    """Task was created."""

    task_name: str
    workflow_id: UUID


@dataclass
class TaskQueued(DomainEvent):
    """Task was queued for execution."""

    workflow_id: UUID


@dataclass
class TaskStarted(DomainEvent):
    """Task execution started."""

    workflow_id: UUID


@dataclass
class TaskCompleted(DomainEvent):
    """Task completed successfully."""

    workflow_id: UUID
    duration_seconds: float
    result: dict[str, Any]


@dataclass
class TaskFailed(DomainEvent):
    """Task failed."""

    workflow_id: UUID
    error_message: str
    retry_count: int


@dataclass
class TaskRetrying(DomainEvent):
    """Task is retrying after failure."""

    workflow_id: UUID
    retry_count: int
    max_retries: int


@dataclass
class TaskCancelled(DomainEvent):
    """Task was cancelled."""

    workflow_id: UUID


@dataclass
class TaskSkipped(DomainEvent):
    """Task was skipped."""

    workflow_id: UUID


@dataclass
class TaskTimeout(DomainEvent):
    """Task exceeded timeout."""

    workflow_id: UUID
    timeout_seconds: int


@dataclass
class TaskStatusChanged(DomainEvent):
    """Task status changed."""

    workflow_id: UUID
    old_status: TaskStatusEnum
    new_status: TaskStatusEnum

