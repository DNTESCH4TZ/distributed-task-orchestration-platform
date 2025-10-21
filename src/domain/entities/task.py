"""
Task Entity - Core domain model for task execution.

A Task represents a single unit of work in a workflow.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from src.core.constants import TaskStatusEnum
from src.core.exceptions import InvalidEntityStateError, MaxRetryExceededError
from src.domain.entities.base import BaseEntity
from src.domain.value_objects.retry_policy import RetryPolicy
from src.domain.value_objects.task_config import TaskConfig
from src.domain.value_objects.task_status import TaskStatus


class Task(BaseEntity):
    """
    Task entity representing a single executable unit.

    Aggregate root for task execution context.
    """

    def __init__(
        self,
        name: str,
        config: TaskConfig,
        payload: dict[str, Any],
        workflow_id: UUID,
        id: UUID | None = None,
        dependencies: list[UUID] | None = None,
        compensation_task_id: UUID | None = None,
    ) -> None:
        """
        Initialize task.

        Args:
            name: Human-readable task name
            config: Task configuration (type, timeout, retry policy)
            payload: Task input data
            workflow_id: Parent workflow ID
            id: Task ID (generated if None)
            dependencies: List of task IDs this task depends on
            compensation_task_id: Task to run if this task needs compensation
        """
        super().__init__(id)
        self._name = name
        self._config = config
        self._payload = payload
        self._workflow_id = workflow_id
        self._dependencies = dependencies or []
        self._compensation_task_id = compensation_task_id

        # Execution state
        self._status = TaskStatus(
            status=TaskStatusEnum.PENDING,
            updated_at=datetime.utcnow(),
        )
        self._result: dict[str, Any] | None = None
        self._error: str | None = None
        self._retry_count = 0
        self._started_at: datetime | None = None
        self._completed_at: datetime | None = None

    # ========================================
    # Properties
    # ========================================

    @property
    def name(self) -> str:
        """Get task name."""
        return self._name

    @property
    def config(self) -> TaskConfig:
        """Get task configuration."""
        return self._config

    @property
    def payload(self) -> dict[str, Any]:
        """Get task payload."""
        return self._payload

    @property
    def workflow_id(self) -> UUID:
        """Get parent workflow ID."""
        return self._workflow_id

    @property
    def dependencies(self) -> list[UUID]:
        """Get task dependencies."""
        return self._dependencies.copy()

    @property
    def compensation_task_id(self) -> UUID | None:
        """Get compensation task ID."""
        return self._compensation_task_id

    @property
    def status(self) -> TaskStatus:
        """Get current status."""
        return self._status

    @property
    def result(self) -> dict[str, Any] | None:
        """Get task result."""
        return self._result

    @property
    def error(self) -> str | None:
        """Get error message."""
        return self._error

    @property
    def retry_count(self) -> int:
        """Get retry attempt count."""
        return self._retry_count

    @property
    def started_at(self) -> datetime | None:
        """Get start timestamp."""
        return self._started_at

    @property
    def completed_at(self) -> datetime | None:
        """Get completion timestamp."""
        return self._completed_at

    # ========================================
    # Business Logic
    # ========================================

    def start(self) -> None:
        """
        Mark task as started.

        Raises:
            InvalidEntityStateError: If task is not in PENDING or QUEUED state
        """
        if not self._status.is_waiting():
            raise InvalidEntityStateError(
                f"Cannot start task in {self._status.status} state"
            )

        self._status = TaskStatus(
            status=TaskStatusEnum.RUNNING,
            updated_at=datetime.utcnow(),
        )
        self._started_at = datetime.utcnow()
        self._mark_updated()

    def complete(self, result: dict[str, Any]) -> None:
        """
        Mark task as successfully completed.

        Args:
            result: Task execution result

        Raises:
            InvalidEntityStateError: If task is not running
        """
        if not self._status.is_active():
            raise InvalidEntityStateError(
                f"Cannot complete task in {self._status.status} state"
            )

        self._status = TaskStatus(
            status=TaskStatusEnum.SUCCEEDED,
            updated_at=datetime.utcnow(),
            message="Task completed successfully",
        )
        self._result = result
        self._completed_at = datetime.utcnow()
        self._mark_updated()

    def fail(self, error: str) -> None:
        """
        Mark task as failed.

        Automatically transitions to RETRYING if retries are available,
        otherwise transitions to FAILED.

        Args:
            error: Error message

        Raises:
            InvalidEntityStateError: If task is not running
        """
        if not self._status.is_active():
            raise InvalidEntityStateError(
                f"Cannot fail task in {self._status.status} state"
            )

        self._error = error

        # Check if we can retry
        if self._can_retry():
            self._retry_count += 1
            self._status = TaskStatus(
                status=TaskStatusEnum.RETRYING,
                updated_at=datetime.utcnow(),
                message=f"Retry {self._retry_count}/{self._config.retry_policy.max_retries}",
            )
        else:
            self._status = TaskStatus(
                status=TaskStatusEnum.FAILED,
                updated_at=datetime.utcnow(),
                message=error,
            )
            self._completed_at = datetime.utcnow()

        self._mark_updated()

    def retry(self) -> None:
        """
        Retry failed task.

        Raises:
            InvalidEntityStateError: If task cannot be retried
            MaxRetryExceededError: If max retries exceeded
        """
        if not self._status.can_retry():
            raise InvalidEntityStateError(
                f"Cannot retry task in {self._status.status} state"
            )

        if not self._can_retry():
            raise MaxRetryExceededError(
                f"Max retries ({self._config.retry_policy.max_retries}) exceeded"
            )

        self._retry_count += 1
        self._status = TaskStatus(
            status=TaskStatusEnum.RUNNING,
            updated_at=datetime.utcnow(),
            message=f"Retry attempt {self._retry_count}",
        )
        self._started_at = datetime.utcnow()
        self._mark_updated()

    def cancel(self) -> None:
        """
        Cancel task execution.

        Raises:
            InvalidEntityStateError: If task is already in terminal state
        """
        if self._status.is_terminal():
            raise InvalidEntityStateError(
                f"Cannot cancel task in {self._status.status} state"
            )

        self._status = TaskStatus(
            status=TaskStatusEnum.CANCELLED,
            updated_at=datetime.utcnow(),
            message="Task cancelled by user",
        )
        self._completed_at = datetime.utcnow()
        self._mark_updated()

    def skip(self, mock_result: dict[str, Any] | None = None) -> None:
        """
        Skip task execution with optional mock result.

        Args:
            mock_result: Optional mock result for dependent tasks
        """
        self._status = TaskStatus(
            status=TaskStatusEnum.SKIPPED,
            updated_at=datetime.utcnow(),
            message="Task skipped",
        )
        self._result = mock_result or {}
        self._completed_at = datetime.utcnow()
        self._mark_updated()

    def timeout(self) -> None:
        """Mark task as timed out."""
        self._status = TaskStatus(
            status=TaskStatusEnum.TIMEOUT,
            updated_at=datetime.utcnow(),
            message=f"Task exceeded timeout of {self._config.timeout_seconds}s",
        )
        self._error = "Task execution timeout"
        self._completed_at = datetime.utcnow()
        self._mark_updated()

    def queue(self) -> None:
        """Mark task as queued for execution."""
        if self._status.status != TaskStatusEnum.PENDING:
            raise InvalidEntityStateError(
                f"Cannot queue task in {self._status.status} state"
            )

        self._status = TaskStatus(
            status=TaskStatusEnum.QUEUED,
            updated_at=datetime.utcnow(),
        )
        self._mark_updated()

    # ========================================
    # Helper Methods
    # ========================================

    def _can_retry(self) -> bool:
        """Check if task can be retried."""
        retry_policy = self._config.retry_policy
        return (
            retry_policy.enabled
            and self._retry_count < retry_policy.max_retries
        )

    def has_dependencies(self) -> bool:
        """Check if task has dependencies."""
        return len(self._dependencies) > 0

    def is_ready_to_execute(self, completed_task_ids: set[UUID]) -> bool:
        """
        Check if all dependencies are completed.

        Args:
            completed_task_ids: Set of completed task IDs

        Returns:
            True if all dependencies are completed
        """
        if not self.has_dependencies():
            return True
        return all(dep_id in completed_task_ids for dep_id in self._dependencies)

    def get_execution_duration(self) -> float | None:
        """
        Get task execution duration in seconds.

        Returns:
            Duration in seconds, or None if not completed
        """
        if self._started_at is None or self._completed_at is None:
            return None
        return (self._completed_at - self._started_at).total_seconds()

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Task(id={self.id}, name={self._name}, "
            f"status={self._status.status}, retry={self._retry_count})"
        )

