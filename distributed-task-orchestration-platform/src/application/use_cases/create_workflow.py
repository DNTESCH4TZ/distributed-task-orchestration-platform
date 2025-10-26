"""
Create Workflow Use Case.

Handles workflow creation with validation and persistence.
"""

from typing import Any
from uuid import UUID

from src.core.constants import ExecutionModeEnum, PriorityEnum, TaskTypeEnum
from src.domain.entities.task import Task
from src.domain.entities.workflow import Workflow
from src.domain.repositories.workflow_repository import IWorkflowRepository
from src.domain.value_objects.retry_policy import RetryPolicy, RetryStrategyEnum
from src.domain.value_objects.task_config import TaskConfig


class CreateWorkflowUseCase:
    """
    Use case for creating a new workflow.

    Validates input, creates domain entities, persists to database.
    """

    def __init__(self, workflow_repository: IWorkflowRepository) -> None:
        """
        Initialize use case.

        Args:
            workflow_repository: Repository for workflow persistence
        """
        self._workflow_repo = workflow_repository

    async def execute(
        self,
        name: str,
        description: str,
        tasks_config: list[dict[str, Any]],
        execution_mode: ExecutionModeEnum = ExecutionModeEnum.DAG,
        parent_workflow_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Workflow:
        """
        Create a new workflow with tasks.

        Args:
            name: Workflow name
            description: Workflow description
            tasks_config: List of task configurations
            execution_mode: How to execute tasks (DAG/sequential/parallel)
            parent_workflow_id: Parent workflow ID for nested workflows
            metadata: Additional metadata

        Returns:
            Created workflow entity

        Raises:
            WorkflowValidationError: If validation fails
        """
        # Create workflow entity
        workflow = Workflow(
            name=name,
            description=description,
            execution_mode=execution_mode,
            parent_workflow_id=parent_workflow_id,
            metadata=metadata or {},
        )

        # Create and add tasks
        for task_cfg in tasks_config:
            task = self._create_task_from_config(workflow.id, task_cfg)
            workflow.add_task(task)

        # Persist to database
        await self._workflow_repo.save(workflow)

        return workflow

    def _create_task_from_config(
        self,
        workflow_id: UUID,
        config: dict[str, Any],
    ) -> Task:
        """
        Create task entity from configuration dict.

        Args:
            workflow_id: Parent workflow ID
            config: Task configuration

        Returns:
            Task entity
        """
        # Parse retry policy
        retry_config = config.get("retry", {})
        retry_policy = RetryPolicy(
            enabled=retry_config.get("enabled", True),
            max_retries=retry_config.get("max_retries", 3),
            strategy=RetryStrategyEnum(
                retry_config.get("strategy", "exponential")
            ),
            backoff_base=retry_config.get("backoff_base", 2),
            backoff_max=retry_config.get("backoff_max", 60),
        )

        # Create task config
        task_config = TaskConfig(
            task_type=TaskTypeEnum(config["type"]),
            timeout_seconds=config.get("timeout", 300),
            priority=PriorityEnum(config.get("priority", "normal")),
            retry_policy=retry_policy,
            idempotency_key=config.get("idempotency_key"),
            max_parallel_instances=config.get("max_parallel_instances", 1),
        )

        # Create task
        return Task(
            name=config["name"],
            config=task_config,
            payload=config.get("payload", {}),
            workflow_id=workflow_id,
            dependencies=config.get("dependencies", []),
            compensation_task_id=config.get("compensation_task_id"),
        )

