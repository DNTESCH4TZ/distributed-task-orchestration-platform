"""
Task Repository Interface.

Defines contract for task persistence (Dependency Inversion Principle).
"""

from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from src.core.constants import TaskStatusEnum
from src.domain.entities.task import Task


class ITaskRepository(ABC):
    """Interface for task persistence operations."""

    @abstractmethod
    async def save(self, task: Task) -> None:
        """
        Save or update task.

        Args:
            task: Task entity to persist
        """
        pass

    @abstractmethod
    async def save_many(self, tasks: List[Task]) -> None:
        """
        Save multiple tasks in batch (performance optimization).

        Args:
            tasks: List of task entities
        """
        pass

    @abstractmethod
    async def get_by_id(self, task_id: UUID) -> Task | None:
        """
        Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task entity or None if not found
        """
        pass

    @abstractmethod
    async def get_many(self, task_ids: List[UUID]) -> List[Task]:
        """
        Get multiple tasks by IDs (batch operation).

        Args:
            task_ids: List of task IDs

        Returns:
            List of task entities
        """
        pass

    @abstractmethod
    async def get_by_workflow(self, workflow_id: UUID) -> List[Task]:
        """
        Get all tasks for a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            List of task entities
        """
        pass

    @abstractmethod
    async def get_by_status(
        self,
        status: TaskStatusEnum,
        limit: int = 100,
    ) -> List[Task]:
        """
        Get tasks by status.

        Args:
            status: Task status to filter by
            limit: Maximum number of tasks

        Returns:
            List of task entities
        """
        pass

    @abstractmethod
    async def get_ready_tasks(self, workflow_id: UUID) -> List[Task]:
        """
        Get tasks ready to execute for a workflow.

        A task is ready if:
        - Status is PENDING or QUEUED
        - All dependencies are completed

        Args:
            workflow_id: Workflow ID

        Returns:
            List of ready task entities
        """
        pass

    @abstractmethod
    async def delete(self, task_id: UUID) -> bool:
        """
        Delete task.

        Args:
            task_id: Task ID

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def exists(self, task_id: UUID) -> bool:
        """
        Check if task exists.

        Args:
            task_id: Task ID

        Returns:
            True if exists, False otherwise
        """
        pass

