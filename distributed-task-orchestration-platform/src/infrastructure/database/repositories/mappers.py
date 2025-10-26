"""
Mappers between Domain Entities and Database Models.

Handles bidirectional conversion with proper data transformation.
"""

from src.core.constants import TaskStatusEnum, WorkflowStatusEnum
from src.domain.entities.task import Task
from src.domain.entities.workflow import Workflow
from src.domain.value_objects.retry_policy import RetryPolicy, RetryStrategyEnum
from src.domain.value_objects.task_config import TaskConfig
from src.domain.value_objects.task_status import TaskStatus
from src.domain.value_objects.workflow_status import WorkflowStatus
from src.infrastructure.database.models.task import TaskModel
from src.infrastructure.database.models.workflow import WorkflowModel


class WorkflowMapper:
    """Maps between Workflow entity and WorkflowModel."""

    @staticmethod
    def to_entity(model: WorkflowModel) -> Workflow:
        """
        Convert database model to domain entity.

        Args:
            model: WorkflowModel from database

        Returns:
            Workflow domain entity
        """
        workflow = Workflow(
            name=model.name,
            description=model.description,
            execution_mode=model.execution_mode,
            id=model.id,
            parent_workflow_id=model.parent_workflow_id,
            metadata=model.metadata,
        )

        # Restore status
        workflow._status = WorkflowStatus(
            status=model.status,
            updated_at=model.updated_at,
        )

        # Restore timestamps
        workflow._created_at = model.created_at
        workflow._updated_at = model.updated_at
        workflow._started_at = model.started_at
        workflow._completed_at = model.completed_at

        # Restore tasks
        for task_model in model.tasks:
            task = TaskMapper.to_entity(task_model)
            workflow._tasks[task.id] = task

        return workflow

    @staticmethod
    def to_model(entity: Workflow) -> WorkflowModel:
        """
        Convert domain entity to database model.

        Args:
            entity: Workflow domain entity

        Returns:
            WorkflowModel for database persistence
        """
        return WorkflowModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            execution_mode=entity.execution_mode,
            status=entity.status.status,
            parent_workflow_id=entity.parent_workflow_id,
            metadata=entity.metadata,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
        )


class TaskMapper:
    """Maps between Task entity and TaskModel."""

    @staticmethod
    def to_entity(model: TaskModel) -> Task:
        """
        Convert database model to domain entity.

        Args:
            model: TaskModel from database

        Returns:
            Task domain entity
        """
        # Reconstruct retry policy
        retry_policy = RetryPolicy(
            enabled=bool(model.retry_enabled),
            max_retries=model.retry_max_attempts,
            strategy=RetryStrategyEnum.EXPONENTIAL,  # Default
            backoff_base=model.retry_backoff_base,
            backoff_max=model.retry_backoff_max,
        )

        # Reconstruct task config
        config = TaskConfig(
            task_type=model.task_type,
            timeout_seconds=model.timeout_seconds,
            priority=model.priority,
            retry_policy=retry_policy,
            idempotency_key=model.idempotency_key,
            max_parallel_instances=model.max_parallel_instances,
        )

        # Create task
        task = Task(
            name=model.name,
            config=config,
            payload=model.payload,
            workflow_id=model.workflow_id,
            id=model.id,
            dependencies=list(model.dependencies) if model.dependencies else [],
            compensation_task_id=model.compensation_task_id,
        )

        # Restore status
        task._status = TaskStatus(
            status=model.status,
            updated_at=model.updated_at,
            message=model.error,
        )

        # Restore execution state
        task._result = model.result
        task._error = model.error
        task._retry_count = model.retry_count
        task._started_at = model.started_at
        task._completed_at = model.completed_at
        task._created_at = model.created_at
        task._updated_at = model.updated_at

        return task

    @staticmethod
    def to_model(entity: Task) -> TaskModel:
        """
        Convert domain entity to database model.

        Args:
            entity: Task domain entity

        Returns:
            TaskModel for database persistence
        """
        return TaskModel(
            id=entity.id,
            name=entity.name,
            task_type=entity.config.task_type,
            workflow_id=entity.workflow_id,
            timeout_seconds=entity.config.timeout_seconds,
            priority=entity.config.priority,
            idempotency_key=entity.config.idempotency_key,
            max_parallel_instances=entity.config.max_parallel_instances,
            retry_enabled=int(entity.config.retry_policy.enabled),
            retry_max_attempts=entity.config.retry_policy.max_retries,
            retry_backoff_base=entity.config.retry_policy.backoff_base,
            retry_backoff_max=entity.config.retry_policy.backoff_max,
            status=entity.status.status,
            retry_count=entity.retry_count,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
            payload=entity.payload,
            result=entity.result,
            error=entity.error,
            dependencies=entity.dependencies,
            compensation_task_id=entity.compensation_task_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

