"""
Task Database Model.

SQLAlchemy model for task persistence.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from src.core.constants import PriorityEnum, TaskStatusEnum, TaskTypeEnum
from src.infrastructure.database.models.base import BaseModel

if TYPE_CHECKING:
    from src.infrastructure.database.models.workflow import WorkflowModel


class TaskModel(BaseModel):
    """
    Task database model.

    Stores task definitions and execution state.
    """

    __tablename__ = "tasks"

    # Basic information
    name = Column(String(255), nullable=False, index=True)
    task_type = Column(Enum(TaskTypeEnum), nullable=False, index=True)

    # Workflow relationship
    workflow_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Task configuration
    timeout_seconds = Column(Integer, nullable=False, default=300)
    priority = Column(
        Enum(PriorityEnum),
        nullable=False,
        default=PriorityEnum.NORMAL,
        index=True,
    )
    idempotency_key = Column(String(255), nullable=True, unique=True, index=True)
    max_parallel_instances = Column(Integer, nullable=False, default=1)

    # Retry configuration
    retry_enabled = Column(Integer, nullable=False, default=1)  # Boolean as int
    retry_max_attempts = Column(Integer, nullable=False, default=3)
    retry_backoff_base = Column(Integer, nullable=False, default=2)
    retry_backoff_max = Column(Integer, nullable=False, default=60)

    # Execution state
    status = Column(
        Enum(TaskStatusEnum),
        nullable=False,
        default=TaskStatusEnum.PENDING,
        index=True,
    )
    retry_count = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Task data (JSONB for flexibility and performance)
    payload = Column(JSONB, nullable=False, default=dict, server_default="{}")
    result = Column(JSONB, nullable=True)
    error = Column(Text, nullable=True)

    # Dependencies (array of task IDs)
    dependencies = Column(
        ARRAY(PostgreSQLUUID(as_uuid=True)),
        nullable=False,
        default=list,
        server_default="{}",
    )

    # Compensation (for Saga pattern)
    compensation_task_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    workflow = relationship("WorkflowModel", back_populates="tasks")
    compensation_task = relationship(
        "TaskModel",
        remote_side="TaskModel.id",
        uselist=False,
    )

    # Indexes for performance (critical for 1M RPS)
    __table_args__ = (
        # Index for finding tasks by workflow and status
        Index("ix_tasks_workflow_status", "workflow_id", "status"),
        # Index for finding pending/queued tasks
        Index("ix_tasks_executable", "status", postgresql_where=(
            status.in_([TaskStatusEnum.PENDING, TaskStatusEnum.QUEUED])
        )),
        # Index for finding failed tasks
        Index("ix_tasks_failed", "status", "workflow_id", postgresql_where=(
            status == TaskStatusEnum.FAILED
        )),
        # Index for idempotency checks (unique)
        Index("ix_tasks_idempotency", "idempotency_key"),
        # Composite index for analytics queries
        Index("ix_tasks_analytics", "task_type", "status", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<TaskModel(id={self.id}, name={self.name}, "
            f"status={self.status}, retry={self.retry_count})>"
        )

