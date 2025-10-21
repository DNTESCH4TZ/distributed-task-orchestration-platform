"""
Task Configuration Value Object.

Immutable value object for task execution configuration.
"""

from dataclasses import dataclass

from src.core.constants import PriorityEnum, TaskTypeEnum
from src.domain.value_objects.retry_policy import RetryPolicy


@dataclass(frozen=True)
class TaskConfig:
    """Task execution configuration."""

    task_type: TaskTypeEnum
    timeout_seconds: int
    priority: PriorityEnum
    retry_policy: RetryPolicy
    idempotency_key: str | None = None
    max_parallel_instances: int = 1  # How many instances can run in parallel

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.timeout_seconds <= 0:
            raise ValueError("Timeout must be positive")
        if self.max_parallel_instances < 1:
            raise ValueError("Max parallel instances must be at least 1")

    @property
    def is_idempotent(self) -> bool:
        """Check if task has idempotency key configured."""
        return self.idempotency_key is not None

