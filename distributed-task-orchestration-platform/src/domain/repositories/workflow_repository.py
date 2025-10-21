"""
Workflow Repository Interface.

Defines contract for workflow persistence (Dependency Inversion Principle).
Implementations will be in infrastructure layer.
"""

from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from src.domain.entities.workflow import Workflow


class IWorkflowRepository(ABC):
    """Interface for workflow persistence operations."""

    @abstractmethod
    async def save(self, workflow: Workflow) -> None:
        """
        Save or update workflow.

        Args:
            workflow: Workflow entity to persist
        """
        pass

    @abstractmethod
    async def get_by_id(self, workflow_id: UUID) -> Workflow | None:
        """
        Get workflow by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow entity or None if not found
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def delete(self, workflow_id: UUID) -> bool:
        """
        Delete workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def exists(self, workflow_id: UUID) -> bool:
        """
        Check if workflow exists.

        Args:
            workflow_id: Workflow ID

        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    async def get_active_workflows(self) -> List[Workflow]:
        """
        Get all active (running/paused) workflows.

        Returns:
            List of active workflows
        """
        pass

    @abstractmethod
    async def get_by_parent(self, parent_workflow_id: UUID) -> List[Workflow]:
        """
        Get child workflows of a parent workflow.

        Args:
            parent_workflow_id: Parent workflow ID

        Returns:
            List of child workflows
        """
        pass

