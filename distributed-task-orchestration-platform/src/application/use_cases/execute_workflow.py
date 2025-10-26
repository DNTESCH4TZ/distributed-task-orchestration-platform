"""
Execute Workflow Use Case.

Orchestrates workflow execution following DAG dependencies.
"""

from uuid import UUID

from src.core.exceptions import EntityNotFoundError, InvalidEntityStateError
from src.domain.entities.workflow import Workflow
from src.domain.repositories.task_repository import ITaskRepository
from src.domain.repositories.workflow_repository import IWorkflowRepository


class ExecuteWorkflowUseCase:
    """
    Use case for executing a workflow.

    Handles workflow lifecycle and task scheduling.
    """

    def __init__(
        self,
        workflow_repository: IWorkflowRepository,
        task_repository: ITaskRepository,
    ) -> None:
        """
        Initialize use case.

        Args:
            workflow_repository: Repository for workflow persistence
            task_repository: Repository for task persistence
        """
        self._workflow_repo = workflow_repository
        self._task_repo = task_repository

    async def execute(self, workflow_id: UUID) -> Workflow:
        """
        Start workflow execution.

        Args:
            workflow_id: Workflow ID to execute

        Returns:
            Started workflow entity

        Raises:
            EntityNotFoundError: If workflow not found
            InvalidEntityStateError: If workflow cannot be started
        """
        # Load workflow
        workflow = await self._workflow_repo.get_by_id(workflow_id)
        if workflow is None:
            raise EntityNotFoundError(f"Workflow {workflow_id} not found")

        # Start workflow
        workflow.start()

        # Queue initial tasks (tasks with no dependencies)
        ready_tasks = workflow.get_ready_tasks()
        for task in ready_tasks:
            task.queue()

        # Persist workflow state
        await self._workflow_repo.save(workflow)

        # Persist task states
        if ready_tasks:
            await self._task_repo.save_many(ready_tasks)

        return workflow

    async def get_next_tasks(self, workflow_id: UUID) -> list:
        """
        Get tasks ready to execute for a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            List of tasks ready for execution
        """
        # Use repository optimized query
        return await self._task_repo.get_ready_tasks(workflow_id)

    async def mark_workflow_completed(self, workflow_id: UUID) -> Workflow:
        """
        Mark workflow as completed.

        Args:
            workflow_id: Workflow ID

        Returns:
            Completed workflow

        Raises:
            EntityNotFoundError: If workflow not found
        """
        workflow = await self._workflow_repo.get_by_id(workflow_id)
        if workflow is None:
            raise EntityNotFoundError(f"Workflow {workflow_id} not found")

        workflow.complete()
        await self._workflow_repo.save(workflow)

        return workflow

    async def mark_workflow_failed(
        self,
        workflow_id: UUID,
        error: str,
    ) -> Workflow:
        """
        Mark workflow as failed.

        Args:
            workflow_id: Workflow ID
            error: Error message

        Returns:
            Failed workflow

        Raises:
            EntityNotFoundError: If workflow not found
        """
        workflow = await self._workflow_repo.get_by_id(workflow_id)
        if workflow is None:
            raise EntityNotFoundError(f"Workflow {workflow_id} not found")

        workflow.fail(error)
        await self._workflow_repo.save(workflow)

        return workflow

