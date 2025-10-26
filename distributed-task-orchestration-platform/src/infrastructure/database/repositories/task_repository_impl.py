"""
Task Repository Implementation.

PostgreSQL implementation of ITaskRepository.
"""

from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.constants import TaskStatusEnum
from src.domain.entities.task import Task
from src.domain.repositories.task_repository import ITaskRepository
from src.infrastructure.database.models.task import TaskModel
from src.infrastructure.database.repositories.mappers import TaskMapper


class TaskRepository(ITaskRepository):
    """PostgreSQL implementation of task repository."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository.

        Args:
            session: Async database session
        """
        self._session = session

    async def save(self, task: Task) -> None:
        """
        Save or update task.

        Args:
            task: Task entity to persist
        """
        model = TaskMapper.to_model(task)
        self._session.add(model)
        await self._session.flush()

    async def save_many(self, tasks: List[Task]) -> None:
        """
        Save multiple tasks in batch (performance optimization).

        Args:
            tasks: List of task entities
        """
        models = [TaskMapper.to_model(task) for task in tasks]
        self._session.add_all(models)
        await self._session.flush()

    async def get_by_id(self, task_id: UUID) -> Task | None:
        """
        Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task entity or None if not found
        """
        stmt = select(TaskModel).where(TaskModel.id == task_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return TaskMapper.to_entity(model)

    async def get_many(self, task_ids: List[UUID]) -> List[Task]:
        """
        Get multiple tasks by IDs (batch operation).

        Args:
            task_ids: List of task IDs

        Returns:
            List of task entities
        """
        stmt = select(TaskModel).where(TaskModel.id.in_(task_ids))
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [TaskMapper.to_entity(model) for model in models]

    async def get_by_workflow(self, workflow_id: UUID) -> List[Task]:
        """
        Get all tasks for a workflow.

        Uses index: ix_tasks_workflow_status

        Args:
            workflow_id: Workflow ID

        Returns:
            List of task entities
        """
        stmt = (
            select(TaskModel)
            .where(TaskModel.workflow_id == workflow_id)
            .order_by(TaskModel.created_at)
        )

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [TaskMapper.to_entity(model) for model in models]

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
        stmt = (
            select(TaskModel)
            .where(TaskModel.status == status)
            .limit(limit)
            .order_by(TaskModel.created_at)
        )

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [TaskMapper.to_entity(model) for model in models]

    async def get_ready_tasks(self, workflow_id: UUID) -> List[Task]:
        """
        Get tasks ready to execute for a workflow.

        A task is ready if:
        - Status is PENDING or QUEUED
        - All dependencies are completed

        Uses partial index: ix_tasks_executable

        Args:
            workflow_id: Workflow ID

        Returns:
            List of ready task entities
        """
        # First, get all completed task IDs for this workflow
        completed_stmt = (
            select(TaskModel.id)
            .where(
                TaskModel.workflow_id == workflow_id,
                TaskModel.status.in_([
                    TaskStatusEnum.SUCCEEDED,
                    TaskStatusEnum.FAILED,
                    TaskStatusEnum.CANCELLED,
                    TaskStatusEnum.SKIPPED,
                ])
            )
        )
        result = await self._session.execute(completed_stmt)
        completed_ids = set(result.scalars().all())

        # Get all pending/queued tasks
        pending_stmt = (
            select(TaskModel)
            .where(
                TaskModel.workflow_id == workflow_id,
                TaskModel.status.in_([
                    TaskStatusEnum.PENDING,
                    TaskStatusEnum.QUEUED,
                ])
            )
        )
        result = await self._session.execute(pending_stmt)
        pending_models = result.scalars().all()

        # Filter tasks where all dependencies are completed
        ready_tasks = []
        for model in pending_models:
            task = TaskMapper.to_entity(model)
            if task.is_ready_to_execute(completed_ids):
                ready_tasks.append(task)

        return ready_tasks

    async def delete(self, task_id: UUID) -> bool:
        """
        Delete task.

        Args:
            task_id: Task ID

        Returns:
            True if deleted, False if not found
        """
        stmt = select(TaskModel).where(TaskModel.id == task_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return False

        await self._session.delete(model)
        await self._session.flush()
        return True

    async def exists(self, task_id: UUID) -> bool:
        """
        Check if task exists.

        Args:
            task_id: Task ID

        Returns:
            True if exists, False otherwise
        """
        stmt = select(TaskModel.id).where(TaskModel.id == task_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

