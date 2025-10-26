"""
Workflow Orchestrator Service.

Core service for orchestrating workflow and task execution.
Implements the orchestration pattern for distributed workflows.
"""

import asyncio
import logging
from typing import Any
from uuid import UUID

from src.core.constants import TaskStatusEnum, WorkflowStatusEnum
from src.core.exceptions import WorkflowExecutionError
from src.domain.entities.task import Task
from src.domain.entities.workflow import Workflow
from src.domain.repositories.task_repository import ITaskRepository
from src.domain.repositories.workflow_repository import IWorkflowRepository

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """
    Orchestrates workflow execution.

    Responsibilities:
    - Schedule tasks based on dependencies
    - Monitor task execution
    - Handle task completion/failure
    - Trigger next tasks
    - Complete workflow when all tasks done
    """

    def __init__(
        self,
        workflow_repo: IWorkflowRepository,
        task_repo: ITaskRepository,
    ) -> None:
        """
        Initialize orchestrator.

        Args:
            workflow_repo: Workflow repository
            task_repo: Task repository
        """
        self._workflow_repo = workflow_repo
        self._task_repo = task_repo

    async def start_workflow(self, workflow_id: UUID) -> None:
        """
        Start workflow execution.

        Queues all root tasks (no dependencies).

        Args:
            workflow_id: Workflow ID to start

        Raises:
            WorkflowExecutionError: If workflow cannot be started
        """
        workflow = await self._workflow_repo.get_by_id(workflow_id)
        if workflow is None:
            raise WorkflowExecutionError(f"Workflow {workflow_id} not found")

        try:
            # Start workflow
            workflow.start()
            await self._workflow_repo.save(workflow)

            # Queue root tasks
            root_tasks = workflow.get_root_tasks()
            for task in root_tasks:
                task.queue()
                await self._task_repo.save(task)
                logger.info(
                    "Task queued",
                    extra={"task_id": task.id, "workflow_id": workflow_id},
                )

            # Trigger task execution (would be picked up by Celery)
            # TODO: Send to message queue
            logger.info(
                "Workflow started",
                extra={
                    "workflow_id": workflow_id,
                    "root_tasks_count": len(root_tasks),
                },
            )

        except Exception as e:
            logger.error(
                "Failed to start workflow",
                extra={"workflow_id": workflow_id, "error": str(e)},
                exc_info=True,
            )
            workflow.fail(str(e))
            await self._workflow_repo.save(workflow)
            raise WorkflowExecutionError(f"Failed to start workflow: {e}") from e

    async def on_task_completed(
        self,
        task_id: UUID,
        result: dict[str, Any],
    ) -> None:
        """
        Handle task completion.

        Updates task state and schedules dependent tasks.

        Args:
            task_id: Completed task ID
            result: Task execution result

        Raises:
            WorkflowExecutionError: If handling fails
        """
        task = await self._task_repo.get_by_id(task_id)
        if task is None:
            raise WorkflowExecutionError(f"Task {task_id} not found")

        try:
            # Mark task as completed
            task.complete(result)
            await self._task_repo.save(task)

            logger.info(
                "Task completed",
                extra={
                    "task_id": task_id,
                    "workflow_id": task.workflow_id,
                    "duration": task.get_execution_duration(),
                },
            )

            # Check for dependent tasks
            await self._schedule_dependent_tasks(task.workflow_id)

            # Check if workflow is complete
            await self._check_workflow_completion(task.workflow_id)

        except Exception as e:
            logger.error(
                "Failed to handle task completion",
                extra={"task_id": task_id, "error": str(e)},
                exc_info=True,
            )
            raise WorkflowExecutionError(
                f"Failed to handle task completion: {e}"
            ) from e

    async def on_task_failed(
        self,
        task_id: UUID,
        error: str,
    ) -> None:
        """
        Handle task failure.

        Triggers retry or marks workflow as failed.

        Args:
            task_id: Failed task ID
            error: Error message

        Raises:
            WorkflowExecutionError: If handling fails
        """
        task = await self._task_repo.get_by_id(task_id)
        if task is None:
            raise WorkflowExecutionError(f"Task {task_id} not found")

        try:
            # Mark task as failed (auto-transitions to RETRYING if possible)
            task.fail(error)
            await self._task_repo.save(task)

            logger.warning(
                "Task failed",
                extra={
                    "task_id": task_id,
                    "workflow_id": task.workflow_id,
                    "error": error,
                    "retry_count": task.retry_count,
                },
            )

            # If task is terminal (no more retries), fail workflow
            if task.status.is_terminal():
                workflow = await self._workflow_repo.get_by_id(task.workflow_id)
                if workflow:
                    workflow.fail(f"Task {task.name} failed: {error}")
                    await self._workflow_repo.save(workflow)

                    logger.error(
                        "Workflow failed due to task failure",
                        extra={
                            "workflow_id": task.workflow_id,
                            "failed_task_id": task_id,
                        },
                    )

        except Exception as e:
            logger.error(
                "Failed to handle task failure",
                extra={"task_id": task_id, "error": str(e)},
                exc_info=True,
            )
            raise WorkflowExecutionError(
                f"Failed to handle task failure: {e}"
            ) from e

    async def _schedule_dependent_tasks(self, workflow_id: UUID) -> None:
        """
        Schedule tasks that are now ready to execute.

        Args:
            workflow_id: Workflow ID
        """
        ready_tasks = await self._task_repo.get_ready_tasks(workflow_id)

        for task in ready_tasks:
            task.queue()
            await self._task_repo.save(task)

            # TODO: Send to message queue for execution
            logger.info(
                "Dependent task queued",
                extra={"task_id": task.id, "workflow_id": workflow_id},
            )

    async def _check_workflow_completion(self, workflow_id: UUID) -> None:
        """
        Check if workflow is complete and update status.

        Args:
            workflow_id: Workflow ID
        """
        workflow = await self._workflow_repo.get_by_id(workflow_id)
        if workflow is None:
            return

        # Get all tasks
        all_tasks = workflow.tasks
        if not all_tasks:
            return

        # Check if all tasks are terminal
        all_terminal = all(task.status.is_terminal() for task in all_tasks)
        if not all_terminal:
            return

        # Check if all succeeded
        all_succeeded = all(
            task.status.status == TaskStatusEnum.SUCCEEDED
            for task in all_tasks
        )

        if all_succeeded:
            workflow.complete()
            logger.info(
                "Workflow completed successfully",
                extra={
                    "workflow_id": workflow_id,
                    "duration": workflow.get_execution_duration(),
                    "tasks_count": len(all_tasks),
                },
            )
        else:
            # Find failed task
            failed_task = next(
                (t for t in all_tasks if t.status.status == TaskStatusEnum.FAILED),
                None,
            )
            error_msg = failed_task.error if failed_task else "Unknown error"
            workflow.fail(error_msg)

            logger.error(
                "Workflow completed with failures",
                extra={"workflow_id": workflow_id, "error": error_msg},
            )

        await self._workflow_repo.save(workflow)

    async def pause_workflow(self, workflow_id: UUID) -> None:
        """
        Pause workflow execution.

        Args:
            workflow_id: Workflow ID to pause
        """
        workflow = await self._workflow_repo.get_by_id(workflow_id)
        if workflow is None:
            raise WorkflowExecutionError(f"Workflow {workflow_id} not found")

        workflow.pause()
        await self._workflow_repo.save(workflow)

        logger.info("Workflow paused", extra={"workflow_id": workflow_id})

    async def resume_workflow(self, workflow_id: UUID) -> None:
        """
        Resume paused workflow execution.

        Args:
            workflow_id: Workflow ID to resume
        """
        workflow = await self._workflow_repo.get_by_id(workflow_id)
        if workflow is None:
            raise WorkflowExecutionError(f"Workflow {workflow_id} not found")

        workflow.resume()
        await self._workflow_repo.save(workflow)

        # Re-schedule ready tasks
        await self._schedule_dependent_tasks(workflow_id)

        logger.info("Workflow resumed", extra={"workflow_id": workflow_id})

    async def cancel_workflow(self, workflow_id: UUID) -> None:
        """
        Cancel workflow execution.

        Args:
            workflow_id: Workflow ID to cancel
        """
        workflow = await self._workflow_repo.get_by_id(workflow_id)
        if workflow is None:
            raise WorkflowExecutionError(f"Workflow {workflow_id} not found")

        # Cancel workflow
        workflow.cancel()
        await self._workflow_repo.save(workflow)

        # Cancel all running tasks
        running_tasks = [
            task
            for task in workflow.tasks
            if task.status.is_active() or task.status.is_waiting()
        ]

        for task in running_tasks:
            task.cancel()
            await self._task_repo.save(task)

        logger.info(
            "Workflow cancelled",
            extra={"workflow_id": workflow_id, "cancelled_tasks": len(running_tasks)},
        )

