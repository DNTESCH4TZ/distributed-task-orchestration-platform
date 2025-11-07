"""
Initial database schema.

Creates workflows and tasks tables with indexes.

Revision ID: 001
Revises: 
Create Date: 2025-10-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial schema."""
    # Create workflows table
    op.create_table(
        "workflows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "execution_mode",
            sa.Enum("sequential", "parallel", "dag", name="executionmodeenum"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "pending",
                "running",
                "paused",
                "succeeded",
                "failed",
                "cancelled",
                "compensating",
                "compensated",
                name="workflowstatusenum",
            ),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "parent_workflow_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflows.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Create tasks table
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "task_type",
            sa.Enum(
                "http",
                "python",
                "shell",
                "sql",
                "webhook",
                "human",
                "subworkflow",
                name="tasktypeenum",
            ),
            nullable=False,
        ),
        sa.Column(
            "workflow_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflows.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False),
        sa.Column(
            "priority",
            sa.Enum("low", "normal", "high", "critical", name="priorityenum"),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(255), nullable=True, unique=True),
        sa.Column("max_parallel_instances", sa.Integer(), nullable=False),
        sa.Column("retry_enabled", sa.Integer(), nullable=False),
        sa.Column("retry_max_attempts", sa.Integer(), nullable=False),
        sa.Column("retry_backoff_base", sa.Integer(), nullable=False),
        sa.Column("retry_backoff_max", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "queued",
                "running",
                "succeeded",
                "failed",
                "retrying",
                "cancelled",
                "skipped",
                "timeout",
                name="taskstatusenum",
            ),
            nullable=False,
        ),
        sa.Column("retry_count", sa.Integer(), nullable=False, default=0),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "dependencies",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "compensation_task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tasks.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Create indexes for workflows
    op.create_index("ix_workflows_id", "workflows", ["id"])
    op.create_index("ix_workflows_name", "workflows", ["name"])
    op.create_index("ix_workflows_status", "workflows", ["status"])
    op.create_index("ix_workflows_created_at", "workflows", ["created_at"])
    op.create_index("ix_workflows_updated_at", "workflows", ["updated_at"])
    op.create_index("ix_workflows_parent", "workflows", ["parent_workflow_id"])
    op.create_index(
        "ix_workflows_status_created", "workflows", ["status", "created_at"]
    )

    # Partial index for active workflows (performance optimization)
    op.create_index(
        "ix_workflows_active",
        "workflows",
        ["status"],
        postgresql_where=sa.text("status IN ('running', 'paused')"),
    )

    # Create indexes for tasks
    op.create_index("ix_tasks_id", "tasks", ["id"])
    op.create_index("ix_tasks_name", "tasks", ["name"])
    op.create_index("ix_tasks_task_type", "tasks", ["task_type"])
    op.create_index("ix_tasks_workflow_id", "tasks", ["workflow_id"])
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_priority", "tasks", ["priority"])
    op.create_index("ix_tasks_idempotency", "tasks", ["idempotency_key"])
    op.create_index("ix_tasks_created_at", "tasks", ["created_at"])
    op.create_index("ix_tasks_updated_at", "tasks", ["updated_at"])
    op.create_index("ix_tasks_workflow_status", "tasks", ["workflow_id", "status"])
    op.create_index(
        "ix_tasks_analytics", "tasks", ["task_type", "status", "created_at"]
    )

    # Partial index for executable tasks (performance optimization)
    op.create_index(
        "ix_tasks_executable",
        "tasks",
        ["status"],
        postgresql_where=sa.text("status IN ('pending', 'queued')"),
    )

    # Partial index for failed tasks (performance optimization)
    op.create_index(
        "ix_tasks_failed",
        "tasks",
        ["status", "workflow_id"],
        postgresql_where=sa.text("status = 'failed'"),
    )


def downgrade() -> None:
    """Drop all tables and indexes."""
    op.drop_table("tasks")
    op.drop_table("workflows")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS executionmodeenum")
    op.execute("DROP TYPE IF EXISTS workflowstatusenum")
    op.execute("DROP TYPE IF EXISTS tasktypeenum")
    op.execute("DROP TYPE IF EXISTS priorityenum")
    op.execute("DROP TYPE IF EXISTS taskstatusenum")

