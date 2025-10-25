"""
Workflow API Endpoints.

CRUD operations and lifecycle management for workflows.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.workflow_orchestrator import WorkflowOrchestrator
from src.application.use_cases.create_workflow import CreateWorkflowUseCase
from src.application.use_cases.execute_workflow import ExecuteWorkflowUseCase
from src.core.constants import ExecutionModeEnum, WorkflowStatusEnum
from src.infrastructure.database.base import get_db
from src.infrastructure.database.repositories.task_repository_impl import TaskRepository
from src.infrastructure.database.repositories.workflow_repository_impl import (
    WorkflowRepository,
)

router = APIRouter()


# ========================================
# Request/Response Models
# ========================================


class TaskConfigRequest(BaseModel):
    """Task configuration in workflow creation request."""

    name: str = Field(..., description="Task name")
    type: str = Field(..., description="Task type (http/python/sql/etc)")
    payload: dict[str, Any] = Field(default_factory=dict, description="Task payload")
    timeout: int = Field(default=300, description="Timeout in seconds")
    priority: str = Field(default="normal", description="Task priority")
    dependencies: list[UUID] = Field(
        default_factory=list, description="Task dependencies (IDs)"
    )
    retry: dict[str, Any] = Field(default_factory=dict, description="Retry config")
    idempotency_key: str | None = Field(None, description="Idempotency key")
    compensation_task_id: UUID | None = Field(None, description="Compensation task")


class CreateWorkflowRequest(BaseModel):
    """Create workflow request."""

    name: str = Field(..., min_length=1, max_length=255, description="Workflow name")
    description: str = Field(..., min_length=1, description="Workflow description")
    tasks: list[TaskConfigRequest] = Field(..., min_items=1, description="Tasks")
    execution_mode: ExecutionModeEnum = Field(
        default=ExecutionModeEnum.DAG, description="Execution mode"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class WorkflowResponse(BaseModel):
    """Workflow response model."""

    id: UUID
    name: str
    description: str
    status: WorkflowStatusEnum
    execution_mode: ExecutionModeEnum
    tasks_count: int
    progress: float
    created_at: str
    started_at: str | None
    completed_at: str | None
    duration_seconds: float | None
    metadata: dict[str, Any]

    model_config = {"from_attributes": True}


# ========================================
# Dependency Injection
# ========================================


async def get_workflow_orchestrator(
    db: AsyncSession = Depends(get_db),
) -> WorkflowOrchestrator:
    """Get workflow orchestrator instance."""
    return WorkflowOrchestrator(
        workflow_repo=WorkflowRepository(db),
        task_repo=TaskRepository(db),
    )


async def get_create_workflow_use_case(
    db: AsyncSession = Depends(get_db),
) -> CreateWorkflowUseCase:
    """Get create workflow use case instance."""
    return CreateWorkflowUseCase(workflow_repo=WorkflowRepository(db))


async def get_execute_workflow_use_case(
    db: AsyncSession = Depends(get_db),
) -> ExecuteWorkflowUseCase:
    """Get execute workflow use case instance."""
    return ExecuteWorkflowUseCase(
        workflow_repo=WorkflowRepository(db),
        task_repo=TaskRepository(db),
    )


# ========================================
# Endpoints
# ========================================


@router.post(
    "/workflows",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create workflow",
    description="Create a new workflow with tasks",
)
async def create_workflow(
    request: CreateWorkflowRequest,
    use_case: CreateWorkflowUseCase = Depends(get_create_workflow_use_case),
) -> WorkflowResponse:
    """
    Create a new workflow.

    Creates workflow with tasks and validates DAG structure.
    """
    try:
        # Convert request to use case format
        tasks_config = [task.model_dump() for task in request.tasks]

        # Create workflow
        workflow = await use_case.execute(
            name=request.name,
            description=request.description,
            tasks_config=tasks_config,
            execution_mode=request.execution_mode,
            metadata=request.metadata,
        )

        return WorkflowResponse(
            id=workflow.id,
            name=workflow.name,
            description=workflow.description,
            status=workflow.status.status,
            execution_mode=workflow.execution_mode,
            tasks_count=len(workflow.tasks),
            progress=workflow.get_progress(),
            created_at=workflow.created_at.isoformat(),
            started_at=workflow.started_at.isoformat() if workflow.started_at else None,
            completed_at=(
                workflow.completed_at.isoformat() if workflow.completed_at else None
            ),
            duration_seconds=workflow.get_execution_duration(),
            metadata=workflow.metadata,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/workflows/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Get workflow",
    description="Get workflow by ID with full details",
)
async def get_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    """Get workflow details."""
    repo = WorkflowRepository(db)
    workflow = await repo.get_by_id(workflow_id)

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found",
        )

    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        status=workflow.status.status,
        execution_mode=workflow.execution_mode,
        tasks_count=len(workflow.tasks),
        progress=workflow.get_progress(),
        created_at=workflow.created_at.isoformat(),
        started_at=workflow.started_at.isoformat() if workflow.started_at else None,
        completed_at=(
            workflow.completed_at.isoformat() if workflow.completed_at else None
        ),
        duration_seconds=workflow.get_execution_duration(),
        metadata=workflow.metadata,
    )


@router.post(
    "/workflows/{workflow_id}/start",
    response_model=WorkflowResponse,
    summary="Start workflow",
    description="Start workflow execution",
)
async def start_workflow(
    workflow_id: UUID,
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    """Start workflow execution."""
    try:
        await orchestrator.start_workflow(workflow_id)

        # Reload workflow
        repo = WorkflowRepository(db)
        workflow = await repo.get_by_id(workflow_id)

        if workflow is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found",
            )

        return WorkflowResponse(
            id=workflow.id,
            name=workflow.name,
            description=workflow.description,
            status=workflow.status.status,
            execution_mode=workflow.execution_mode,
            tasks_count=len(workflow.tasks),
            progress=workflow.get_progress(),
            created_at=workflow.created_at.isoformat(),
            started_at=workflow.started_at.isoformat() if workflow.started_at else None,
            completed_at=(
                workflow.completed_at.isoformat() if workflow.completed_at else None
            ),
            duration_seconds=workflow.get_execution_duration(),
            metadata=workflow.metadata,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/workflows/{workflow_id}/pause",
    response_model=WorkflowResponse,
    summary="Pause workflow",
    description="Pause workflow execution",
)
async def pause_workflow(
    workflow_id: UUID,
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    """Pause workflow execution."""
    await orchestrator.pause_workflow(workflow_id)

    repo = WorkflowRepository(db)
    workflow = await repo.get_by_id(workflow_id)

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found",
        )

    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        status=workflow.status.status,
        execution_mode=workflow.execution_mode,
        tasks_count=len(workflow.tasks),
        progress=workflow.get_progress(),
        created_at=workflow.created_at.isoformat(),
        started_at=workflow.started_at.isoformat() if workflow.started_at else None,
        completed_at=(
            workflow.completed_at.isoformat() if workflow.completed_at else None
        ),
        duration_seconds=workflow.get_execution_duration(),
        metadata=workflow.metadata,
    )


@router.post(
    "/workflows/{workflow_id}/resume",
    response_model=WorkflowResponse,
    summary="Resume workflow",
    description="Resume paused workflow",
)
async def resume_workflow(
    workflow_id: UUID,
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    """Resume paused workflow."""
    await orchestrator.resume_workflow(workflow_id)

    repo = WorkflowRepository(db)
    workflow = await repo.get_by_id(workflow_id)

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found",
        )

    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        status=workflow.status.status,
        execution_mode=workflow.execution_mode,
        tasks_count=len(workflow.tasks),
        progress=workflow.get_progress(),
        created_at=workflow.created_at.isoformat(),
        started_at=workflow.started_at.isoformat() if workflow.started_at else None,
        completed_at=(
            workflow.completed_at.isoformat() if workflow.completed_at else None
        ),
        duration_seconds=workflow.get_execution_duration(),
        metadata=workflow.metadata,
    )


@router.post(
    "/workflows/{workflow_id}/cancel",
    response_model=WorkflowResponse,
    summary="Cancel workflow",
    description="Cancel workflow execution",
)
async def cancel_workflow(
    workflow_id: UUID,
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    """Cancel workflow execution."""
    await orchestrator.cancel_workflow(workflow_id)

    repo = WorkflowRepository(db)
    workflow = await repo.get_by_id(workflow_id)

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found",
        )

    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        status=workflow.status.status,
        execution_mode=workflow.execution_mode,
        tasks_count=len(workflow.tasks),
        progress=workflow.get_progress(),
        created_at=workflow.created_at.isoformat(),
        started_at=workflow.started_at.isoformat() if workflow.started_at else None,
        completed_at=(
            workflow.completed_at.isoformat() if workflow.completed_at else None
        ),
        duration_seconds=workflow.get_execution_duration(),
        metadata=workflow.metadata,
    )


@router.get(
    "/workflows",
    response_model=list[WorkflowResponse],
    summary="List workflows",
    description="Get list of workflows with pagination",
)
async def list_workflows(
    limit: int = Query(default=100, le=1000, description="Max workflows to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
) -> list[WorkflowResponse]:
    """List all workflows with pagination."""
    repo = WorkflowRepository(db)
    workflows = await repo.get_all(limit=limit, offset=offset)

    return [
        WorkflowResponse(
            id=wf.id,
            name=wf.name,
            description=wf.description,
            status=wf.status.status,
            execution_mode=wf.execution_mode,
            tasks_count=len(wf.tasks),
            progress=wf.get_progress(),
            created_at=wf.created_at.isoformat(),
            started_at=wf.started_at.isoformat() if wf.started_at else None,
            completed_at=wf.completed_at.isoformat() if wf.completed_at else None,
            duration_seconds=wf.get_execution_duration(),
            metadata=wf.metadata,
        )
        for wf in workflows
    ]

