"""
Workflow Database Model.

SQLAlchemy model for workflow persistence.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from src.core.constants import ExecutionModeEnum, WorkflowStatusEnum
from src.infrastructure.database.models.base import BaseModel

if TYPE_CHECKING:
    from src.infrastructure.database.models.task import TaskModel


class WorkflowModel(BaseModel):
    """
    Workflow database model.

    Stores workflow definitions and execution state.
    """

    __tablename__ = "workflows"

    # Basic information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    execution_mode = Column(
        Enum(ExecutionModeEnum),
        nullable=False,
        default=ExecutionModeEnum.DAG,
        index=True,
    )

    # Status and lifecycle
    status = Column(
        Enum(WorkflowStatusEnum),
        nullable=False,
        default=WorkflowStatusEnum.DRAFT,
        index=True,
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Nested workflow support
    parent_workflow_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Additional metadata (flexible JSONB for custom fields)
    metadata = Column(JSONB, nullable=False, default=dict, server_default="{}")

    # Relationships
    tasks = relationship(
        "TaskModel",
        back_populates="workflow",
        cascade="all, delete-orphan",
        lazy="selectin",  # Eager loading for performance
    )

    child_workflows = relationship(
        "WorkflowModel",
        backref="parent_workflow",
        remote_side="WorkflowModel.id",
        lazy="select",
    )

    # Indexes for performance (critical for 1M RPS)
    __table_args__ = (
        # Index for finding active workflows
        Index("ix_workflows_active", "status", postgresql_where=(
            status.in_([
                WorkflowStatusEnum.RUNNING,
                WorkflowStatusEnum.PAUSED,
            ])
        )),
        # Index for finding workflows by parent
        Index("ix_workflows_parent", "parent_workflow_id"),
        # Composite index for queries by status and date
        Index("ix_workflows_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<WorkflowModel(id={self.id}, name={self.name}, "
            f"status={self.status})>"
        )

