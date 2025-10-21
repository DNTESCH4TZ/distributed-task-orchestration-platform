"""
Task Status Value Object.

Immutable value object representing task execution status.
"""

from dataclasses import dataclass
from datetime import datetime

from src.core.constants import TaskStatusEnum


@dataclass(frozen=True)
class TaskStatus:
    """Task execution status with metadata."""

    status: TaskStatusEnum
    updated_at: datetime
    message: str | None = None

    def is_terminal(self) -> bool:
        """Check if status is terminal (no further transitions)."""
        return self.status in {
            TaskStatusEnum.SUCCEEDED,
            TaskStatusEnum.FAILED,
            TaskStatusEnum.CANCELLED,
            TaskStatusEnum.SKIPPED,
        }

    def is_active(self) -> bool:
        """Check if task is actively running."""
        return self.status in {
            TaskStatusEnum.RUNNING,
            TaskStatusEnum.RETRYING,
        }

    def is_waiting(self) -> bool:
        """Check if task is waiting to execute."""
        return self.status in {
            TaskStatusEnum.PENDING,
            TaskStatusEnum.QUEUED,
        }

    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.status in {
            TaskStatusEnum.FAILED,
            TaskStatusEnum.TIMEOUT,
        }

