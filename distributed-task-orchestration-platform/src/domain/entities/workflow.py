"""
Workflow Entity - Core domain model for workflow orchestration.

A Workflow is an aggregate root that manages task execution graph.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from src.core.constants import ExecutionModeEnum, WorkflowStatusEnum
from src.core.exceptions import (
    CircularDependencyError,
    InvalidEntityStateError,
    MaxDepthExceededError,
)
from src.domain.entities.base import BaseEntity
from src.domain.entities.task import Task
from src.domain.value_objects.workflow_status import WorkflowStatus


class Workflow(BaseEntity):
    """
    Workflow entity representing a DAG of tasks.

    Aggregate root for workflow execution context.
    Enforces consistency boundaries for task graph.
    """

    def __init__(
        self,
        name: str,
        description: str,
        execution_mode: ExecutionModeEnum = ExecutionModeEnum.DAG,
        id: UUID | None = None,
        parent_workflow_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize workflow.

        Args:
            name: Human-readable workflow name
            description: Workflow description
            execution_mode: How tasks should execute (sequential/parallel/dag)
            id: Workflow ID (generated if None)
            parent_workflow_id: Parent workflow ID for nested workflows
            metadata: Additional metadata
        """
        super().__init__(id)
        self._name = name
        self._description = description
        self._execution_mode = execution_mode
        self._parent_workflow_id = parent_workflow_id
        self._metadata = metadata or {}

        # Workflow state
        self._status = WorkflowStatus(
            status=WorkflowStatusEnum.DRAFT,
            updated_at=datetime.utcnow(),
        )
        self._tasks: dict[UUID, Task] = {}
        self._started_at: datetime | None = None
        self._completed_at: datetime | None = None

        # Validate nesting depth
        self._validate_depth()

    # ========================================
    # Properties
    # ========================================

    @property
    def name(self) -> str:
        """Get workflow name."""
        return self._name

    @property
    def description(self) -> str:
        """Get workflow description."""
        return self._description

    @property
    def execution_mode(self) -> ExecutionModeEnum:
        """Get execution mode."""
        return self._execution_mode

    @property
    def parent_workflow_id(self) -> UUID | None:
        """Get parent workflow ID."""
        return self._parent_workflow_id

    @property
    def metadata(self) -> dict[str, Any]:
        """Get metadata."""
        return self._metadata.copy()

    @property
    def status(self) -> WorkflowStatus:
        """Get current status."""
        return self._status

    @property
    def tasks(self) -> list[Task]:
        """Get all tasks."""
        return list(self._tasks.values())

    @property
    def started_at(self) -> datetime | None:
        """Get start timestamp."""
        return self._started_at

    @property
    def completed_at(self) -> datetime | None:
        """Get completion timestamp."""
        return self._completed_at

    # ========================================
    # Task Management
    # ========================================

    def add_task(self, task: Task) -> None:
        """
        Add task to workflow.

        Args:
            task: Task to add

        Raises:
            InvalidEntityStateError: If workflow is not in DRAFT state
            CircularDependencyError: If adding task creates circular dependency
        """
        if self._status.status != WorkflowStatusEnum.DRAFT:
            raise InvalidEntityStateError(
                f"Cannot add task to workflow in {self._status.status} state"
            )

        # Validate task belongs to this workflow
        if task.workflow_id != self.id:
            raise InvalidEntityStateError(
                "Task workflow_id does not match workflow ID"
            )

        # Check for circular dependencies
        if self._creates_cycle(task):
            raise CircularDependencyError(
                f"Adding task {task.name} would create circular dependency"
            )

        self._tasks[task.id] = task
        self._mark_updated()

    def remove_task(self, task_id: UUID) -> None:
        """
        Remove task from workflow.

        Args:
            task_id: Task ID to remove

        Raises:
            InvalidEntityStateError: If workflow is not in DRAFT state
        """
        if self._status.status != WorkflowStatusEnum.DRAFT:
            raise InvalidEntityStateError(
                f"Cannot remove task from workflow in {self._status.status} state"
            )

        if task_id in self._tasks:
            del self._tasks[task_id]
            self._mark_updated()

    def get_task(self, task_id: UUID) -> Task | None:
        """Get task by ID."""
        return self._tasks.get(task_id)

    # ========================================
    # Workflow Lifecycle
    # ========================================

    def start(self) -> None:
        """
        Start workflow execution.

        Raises:
            InvalidEntityStateError: If workflow cannot be started
        """
        if self._status.status not in {
            WorkflowStatusEnum.DRAFT,
            WorkflowStatusEnum.PENDING,
        }:
            raise InvalidEntityStateError(
                f"Cannot start workflow in {self._status.status} state"
            )

        if not self._tasks:
            raise InvalidEntityStateError("Cannot start workflow with no tasks")

        self._status = WorkflowStatus(
            status=WorkflowStatusEnum.RUNNING,
            updated_at=datetime.utcnow(),
        )
        self._started_at = datetime.utcnow()
        self._mark_updated()

    def complete(self) -> None:
        """
        Mark workflow as successfully completed.

        Raises:
            InvalidEntityStateError: If workflow is not running
        """
        if not self._status.is_active():
            raise InvalidEntityStateError(
                f"Cannot complete workflow in {self._status.status} state"
            )

        self._status = WorkflowStatus(
            status=WorkflowStatusEnum.SUCCEEDED,
            updated_at=datetime.utcnow(),
            message="Workflow completed successfully",
        )
        self._completed_at = datetime.utcnow()
        self._mark_updated()

    def fail(self, error: str) -> None:
        """
        Mark workflow as failed.

        Args:
            error: Error message
        """
        self._status = WorkflowStatus(
            status=WorkflowStatusEnum.FAILED,
            updated_at=datetime.utcnow(),
            message=error,
        )
        self._completed_at = datetime.utcnow()
        self._mark_updated()

    def pause(self) -> None:
        """
        Pause workflow execution.

        Raises:
            InvalidEntityStateError: If workflow cannot be paused
        """
        if not self._status.can_pause():
            raise InvalidEntityStateError(
                f"Cannot pause workflow in {self._status.status} state"
            )

        self._status = WorkflowStatus(
            status=WorkflowStatusEnum.PAUSED,
            updated_at=datetime.utcnow(),
            message="Workflow paused by user",
        )
        self._mark_updated()

    def resume(self) -> None:
        """
        Resume paused workflow.

        Raises:
            InvalidEntityStateError: If workflow cannot be resumed
        """
        if not self._status.can_resume():
            raise InvalidEntityStateError(
                f"Cannot resume workflow in {self._status.status} state"
            )

        self._status = WorkflowStatus(
            status=WorkflowStatusEnum.RUNNING,
            updated_at=datetime.utcnow(),
            message="Workflow resumed",
        )
        self._mark_updated()

    def cancel(self) -> None:
        """
        Cancel workflow execution.

        Raises:
            InvalidEntityStateError: If workflow cannot be cancelled
        """
        if not self._status.can_cancel():
            raise InvalidEntityStateError(
                f"Cannot cancel workflow in {self._status.status} state"
            )

        self._status = WorkflowStatus(
            status=WorkflowStatusEnum.CANCELLED,
            updated_at=datetime.utcnow(),
            message="Workflow cancelled by user",
        )
        self._completed_at = datetime.utcnow()
        self._mark_updated()

    def start_compensation(self) -> None:
        """Start Saga compensation (rollback)."""
        self._status = WorkflowStatus(
            status=WorkflowStatusEnum.COMPENSATING,
            updated_at=datetime.utcnow(),
            message="Starting compensation",
        )
        self._mark_updated()

    def complete_compensation(self) -> None:
        """Complete Saga compensation."""
        self._status = WorkflowStatus(
            status=WorkflowStatusEnum.COMPENSATED,
            updated_at=datetime.utcnow(),
            message="Compensation completed",
        )
        self._completed_at = datetime.utcnow()
        self._mark_updated()

    # ========================================
    # Task Dependency Graph
    # ========================================

    def get_ready_tasks(self) -> list[Task]:
        """
        Get tasks ready to execute (all dependencies completed).

        Returns:
            List of tasks ready for execution
        """
        completed_task_ids = {
            task.id for task in self._tasks.values() if task.status.is_terminal()
        }

        ready_tasks = [
            task
            for task in self._tasks.values()
            if task.status.is_waiting() and task.is_ready_to_execute(completed_task_ids)
        ]

        return ready_tasks

    def get_root_tasks(self) -> list[Task]:
        """Get tasks with no dependencies (entry points)."""
        return [task for task in self._tasks.values() if not task.has_dependencies()]

    def get_dependent_tasks(self, task_id: UUID) -> list[Task]:
        """
        Get tasks that depend on given task.

        Args:
            task_id: Task ID to check

        Returns:
            List of tasks that depend on the given task
        """
        return [
            task
            for task in self._tasks.values()
            if task_id in task.dependencies
        ]

    # ========================================
    # Validation
    # ========================================

    def _validate_depth(self) -> None:
        """
        Validate workflow nesting depth.

        Raises:
            MaxDepthExceededError: If max depth exceeded
        """
        from src.core.constants import MAX_WORKFLOW_DEPTH

        # TODO: Implement depth calculation when we have repository
        # For now, just check if parent exists
        if self._parent_workflow_id:
            # In real implementation, would traverse parent chain
            pass

    def _creates_cycle(self, new_task: Task) -> bool:
        """
        Check if adding task would create circular dependency.

        Uses DFS to detect cycles in dependency graph.

        Args:
            new_task: Task to add

        Returns:
            True if adding task would create cycle
        """
        # Build adjacency list
        graph: dict[UUID, set[UUID]] = {}
        for task in self._tasks.values():
            graph[task.id] = set(task.dependencies)

        # Add new task
        graph[new_task.id] = set(new_task.dependencies)

        # DFS cycle detection
        visited: set[UUID] = set()
        rec_stack: set[UUID] = set()

        def has_cycle(node: UUID) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for task_id in graph:
            if task_id not in visited:
                if has_cycle(task_id):
                    return True

        return False

    # ========================================
    # Metrics
    # ========================================

    def get_progress(self) -> float:
        """
        Get workflow progress percentage.

        Returns:
            Progress from 0.0 to 100.0
        """
        if not self._tasks:
            return 0.0

        completed = sum(
            1 for task in self._tasks.values() if task.status.is_terminal()
        )
        return (completed / len(self._tasks)) * 100.0

    def get_execution_duration(self) -> float | None:
        """
        Get workflow execution duration in seconds.

        Returns:
            Duration in seconds, or None if not completed
        """
        if self._started_at is None:
            return None
        end_time = self._completed_at or datetime.utcnow()
        return (end_time - self._started_at).total_seconds()

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Workflow(id={self.id}, name={self._name}, "
            f"status={self._status.status}, tasks={len(self._tasks)})"
        )

