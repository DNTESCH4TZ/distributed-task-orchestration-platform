"""
Workflow Repository Implementation.

PostgreSQL implementation of IWorkflowRepository.
"""

from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.constants import WorkflowStatusEnum
from src.domain.entities.workflow import Workflow
from src.domain.repositories.workflow_repository import IWorkflowRepository
from src.infrastructure.database.models.workflow import WorkflowModel
from src.infrastructure.database.repositories.mappers import WorkflowMapper


class WorkflowRepository(IWorkflowRepository):
    """PostgreSQL implementation of workflow repository."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository.

        Args:
            session: Async database session
        """
        self._session = session

    async def save(self, workflow: Workflow) -> None:
        """
        Save or update workflow.

        Args:
            workflow: Workflow entity to persist
        """
        # Convert domain entity to database model
        model = WorkflowMapper.to_model(workflow)

        # Merge (upsert) into database
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, workflow_id: UUID) -> Workflow | None:
        """
        Get workflow by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow entity or None if not found
        """
        stmt = (
            select(WorkflowModel)
            .where(WorkflowModel.id == workflow_id)
            .options(selectinload(WorkflowModel.tasks))  # Eager load tasks
        )

        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return WorkflowMapper.to_entity(model)

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Workflow]:
        """
        Get all workflows with pagination.

        Args:
            limit: Maximum number of workflows to return
            offset: Number of workflows to skip

        Returns:
            List of workflow entities
        """
        stmt = (
            select(WorkflowModel)
            .options(selectinload(WorkflowModel.tasks))
            .limit(limit)
            .offset(offset)
            .order_by(WorkflowModel.created_at.desc())
        )

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [WorkflowMapper.to_entity(model) for model in models]

    async def delete(self, workflow_id: UUID) -> bool:
        """
        Delete workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            True if deleted, False if not found
        """
        stmt = select(WorkflowModel).where(WorkflowModel.id == workflow_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return False

        await self._session.delete(model)
        await self._session.flush()
        return True

    async def exists(self, workflow_id: UUID) -> bool:
        """
        Check if workflow exists.

        Args:
            workflow_id: Workflow ID

        Returns:
            True if exists, False otherwise
        """
        stmt = select(WorkflowModel.id).where(WorkflowModel.id == workflow_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_active_workflows(self) -> List[Workflow]:
        """
        Get all active (running/paused) workflows.

        Uses optimized index: ix_workflows_active

        Returns:
            List of active workflows
        """
        stmt = (
            select(WorkflowModel)
            .where(
                WorkflowModel.status.in_([
                    WorkflowStatusEnum.RUNNING,
                    WorkflowStatusEnum.PAUSED,
                ])
            )
            .options(selectinload(WorkflowModel.tasks))
            .order_by(WorkflowModel.created_at.desc())
        )

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [WorkflowMapper.to_entity(model) for model in models]

    async def get_by_parent(self, parent_workflow_id: UUID) -> List[Workflow]:
        """
        Get child workflows of a parent workflow.

        Args:
            parent_workflow_id: Parent workflow ID

        Returns:
            List of child workflows
        """
        stmt = (
            select(WorkflowModel)
            .where(WorkflowModel.parent_workflow_id == parent_workflow_id)
            .options(selectinload(WorkflowModel.tasks))
            .order_by(WorkflowModel.created_at.desc())
        )

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [WorkflowMapper.to_entity(model) for model in models]

