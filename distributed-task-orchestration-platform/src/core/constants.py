"""
Core constants used throughout the application.
"""

from enum import Enum


class TaskStatusEnum(str, Enum):
    """Task execution status."""

    PENDING = "pending"  # Task created, waiting to be picked up
    QUEUED = "queued"  # Task added to queue
    RUNNING = "running"  # Currently executing
    SUCCEEDED = "succeeded"  # Completed successfully
    FAILED = "failed"  # Failed after all retries
    RETRYING = "retrying"  # Failed, will retry
    CANCELLED = "cancelled"  # Manually cancelled
    SKIPPED = "skipped"  # Skipped (conditional execution)
    TIMEOUT = "timeout"  # Exceeded time limit


class WorkflowStatusEnum(str, Enum):
    """Workflow execution status."""

    DRAFT = "draft"  # Created but not started
    PENDING = "pending"  # Waiting to start
    RUNNING = "running"  # Currently executing
    PAUSED = "paused"  # Temporarily paused
    SUCCEEDED = "succeeded"  # All tasks completed successfully
    FAILED = "failed"  # One or more tasks failed
    CANCELLED = "cancelled"  # Manually cancelled
    COMPENSATING = "compensating"  # Running compensation (Saga rollback)
    COMPENSATED = "compensated"  # Compensation completed


class TaskTypeEnum(str, Enum):
    """Type of task to execute."""

    HTTP = "http"  # HTTP API call
    PYTHON = "python"  # Python function execution
    SHELL = "shell"  # Shell command
    SQL = "sql"  # Database query
    WEBHOOK = "webhook"  # Webhook trigger
    HUMAN = "human"  # Requires human approval
    SUBWORKFLOW = "subworkflow"  # Nested workflow


class RetryStrategyEnum(str, Enum):
    """Retry strategy for failed tasks."""

    NONE = "none"  # No retries
    FIXED = "fixed"  # Fixed delay between retries
    EXPONENTIAL = "exponential"  # Exponential backoff
    LINEAR = "linear"  # Linear backoff


class ExecutionModeEnum(str, Enum):
    """Workflow execution mode."""

    SEQUENTIAL = "sequential"  # Tasks run one after another
    PARALLEL = "parallel"  # All tasks run simultaneously
    DAG = "dag"  # Tasks follow dependency graph (default)


class PriorityEnum(str, Enum):
    """Task/Workflow priority."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# ========================================
# Timeouts & Limits (for 1M RPS)
# ========================================

DEFAULT_TASK_TIMEOUT = 300  # 5 minutes
MAX_TASK_TIMEOUT = 3600  # 1 hour
MIN_TASK_TIMEOUT = 1  # 1 second

DEFAULT_RETRY_DELAY = 1  # 1 second
MAX_RETRIES = 5
EXPONENTIAL_BACKOFF_BASE = 2
MAX_EXPONENTIAL_BACKOFF = 300  # 5 minutes

# Connection pool sizes for high throughput
DB_POOL_SIZE = 20
DB_MAX_OVERFLOW = 10
REDIS_POOL_SIZE = 50
CELERY_PREFETCH_MULTIPLIER = 4

# Rate limiting
DEFAULT_RATE_LIMIT_PER_MINUTE = 1000
DEFAULT_RATE_LIMIT_PER_HOUR = 10000

# Workflow constraints
MAX_WORKFLOW_DEPTH = 10  # Max nested workflow levels
MAX_TASKS_PER_WORKFLOW = 1000
MAX_PARALLEL_TASKS = 100

# Retention
WORKFLOW_RETENTION_DAYS = 30
TASK_LOG_RETENTION_DAYS = 7

