"""
Workflow Status Value Object.

Immutable value object representing workflow execution status.
"""

from dataclasses import dataclass
from datetime import datetime

from src.core.constants import WorkflowStatusEnum


@dataclass(frozen=True)
class WorkflowStatus:
    """Workflow execution status with metadata."""

    status: WorkflowStatusEnum
    updated_at: datetime
    message: str | None = None

    def is_terminal(self) -> bool:
        """Check if status is terminal (no further transitions)."""
        return self.status in {
            WorkflowStatusEnum.SUCCEEDED,
            WorkflowStatusEnum.FAILED,
            WorkflowStatusEnum.CANCELLED,
            WorkflowStatusEnum.COMPENSATED,
        }

    def is_active(self) -> bool:
        """Check if workflow is actively running."""
        return self.status in {
            WorkflowStatusEnum.RUNNING,
            WorkflowStatusEnum.COMPENSATING,
        }

    def can_pause(self) -> bool:
        """Check if workflow can be paused."""
        return self.status == WorkflowStatusEnum.RUNNING

    def can_resume(self) -> bool:
        """Check if workflow can be resumed."""
        return self.status == WorkflowStatusEnum.PAUSED

    def can_cancel(self) -> bool:
        """Check if workflow can be cancelled."""
        return self.status in {
            WorkflowStatusEnum.PENDING,
            WorkflowStatusEnum.RUNNING,
            WorkflowStatusEnum.PAUSED,
        }

