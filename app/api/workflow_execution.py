"""
API endpoints dla Workflow Builder - Execution Operations

Ten moduł zawiera endpointy dla walidacji i wykonywania workflow:
- POST /{workflow_id}/validate - Pre-flight validation
- POST /{workflow_id}/execute - Execute workflow
- GET /{workflow_id}/executions - Get execution history

Total endpoints: 3

Konwencje:
- Wszystkie response models używają Pydantic schemas z app/schemas/workflow.py
- Auth wymagany dla wszystkich endpoints (Depends(get_current_user))
- Error handling z proper HTTP status codes (200, 400, 404, 500)
- Polish docstrings
- Logging dla wszystkich operations
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.dependencies import get_current_user
from app.models import User, WorkflowExecution
from app.schemas.workflow import (
    WorkflowExecuteRequest,
    WorkflowExecutionResponse,
    ValidationResult,
)
from app.services.workflows import (
    WorkflowService,
    WorkflowValidator,
    WorkflowExecutor,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Workflows"])


@router.post("/{workflow_id}/validate", response_model=ValidationResult)
async def validate_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pre-flight validation workflow.

    Sprawdza czy workflow jest gotowy do wykonania:
    - Graph structure: DAG, cycles, orphaned nodes, disconnected components
    - Node configs: Required fields, valid values
    - Dependencies: Project exists, personas exist (jeśli wymagane)

    Args:
        workflow_id: UUID workflow
        db: Database session
        current_user: Authenticated user

    Returns:
        ValidationResult {is_valid, errors, warnings}

    Example response:
        {
          "is_valid": false,
          "errors": [
            "Orphaned node detected: node-456 (Generate Personas)",
            "Decision node must have exactly 2 outgoing edges"
          ],
          "warnings": [
            "Large workflow (50+ nodes) may be slow to execute"
          ]
        }

    Example:
        POST /api/v1/workflows/{uuid}/validate
    """
    logger.info(
        f"Validating workflow {workflow_id}",
        extra={"user_id": str(current_user.id), "workflow_id": str(workflow_id)},
    )

    service = WorkflowService(db)

    try:
        # Load workflow
        workflow = await service.get_workflow_by_id(workflow_id, current_user.id)

        # Validate
        validator = WorkflowValidator()
        result = await validator.validate_execution_readiness(workflow, db)

        logger.info(
            "Workflow validation complete",
            extra={
                "workflow_id": str(workflow_id),
                "is_valid": result.is_valid,
                "errors_count": len(result.errors),
                "warnings_count": len(result.warnings),
            },
        )

        return result

    except HTTPException:
        # Re-raise HTTPException (404)
        raise

    except Exception as e:
        logger.error(
            f"Workflow validation error: {e}",
            exc_info=True,
            extra={"workflow_id": str(workflow_id), "user_id": str(current_user.id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Validation failed due to internal error",
        )


@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    workflow_id: UUID,
    data: WorkflowExecuteRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Wykonuje workflow.

    **UWAGA:** Długo działająca operacja (może trwać 3-10 minut dla dużych workflow).
    W produkcji rozważ background task (Celery, Cloud Tasks) dla timeout > 60s.

    Flow:
    1. Validation workflow (graph structure, node configs)
    2. Topological sort nodes (DAG execution order)
    3. Execute nodes sekwencyjnie (MVP - brak parallel execution)
    4. Save results do WorkflowExecution

    Args:
        workflow_id: UUID workflow
        data: Execution options (optional, MVP: tylko execution_mode)
        db: Database session
        current_user: Authenticated user

    Returns:
        WorkflowExecutionResponse z statusem i results

    Raises:
        400: Jeśli validation fails
        404: Jeśli workflow nie istnieje
        500: Jeśli execution fails

    Example:
        POST /api/v1/workflows/{uuid}/execute
        {
          "execution_mode": "sequential"
        }

    Response:
        {
          "id": "execution-uuid",
          "workflow_id": "workflow-uuid",
          "status": "completed",
          "result_data": {
            "personas_generated": 20,
            "focus_group_completed": true,
            "analysis_report": "..."
          },
          "started_at": "2025-11-04T10:00:00Z",
          "completed_at": "2025-11-04T10:05:30Z"
        }
    """
    logger.info(
        f"Starting execution of workflow {workflow_id}",
        extra={"user_id": str(current_user.id), "workflow_id": str(workflow_id)},
    )

    executor = WorkflowExecutor(db)

    try:
        execution = await executor.execute_workflow(workflow_id, current_user.id)

        logger.info(
            f"Workflow execution {execution.status}",
            extra={
                "workflow_id": str(workflow_id),
                "execution_id": str(execution.id),
                "status": execution.status,
                "user_id": str(current_user.id),
            },
        )

        return execution

    except ValueError as e:
        # Validation error
        logger.warning(
            f"Workflow execution validation failed: {e}",
            extra={"workflow_id": str(workflow_id), "user_id": str(current_user.id)},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except HTTPException:
        # Re-raise HTTPException (404)
        raise

    except Exception as e:
        # Execution error
        logger.error(
            f"Workflow execution failed: {e}",
            exc_info=True,
            extra={"workflow_id": str(workflow_id), "user_id": str(current_user.id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}",
        )


@router.get("/{workflow_id}/executions", response_model=list[WorkflowExecutionResponse])
async def get_execution_history(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pobiera historię wykonań workflow.

    Zwraca wszystkie executions dla danego workflow (sorted by started_at desc).
    Użyteczne dla:
    - Tracking progress previous runs
    - Debugging failed executions
    - Comparing results across executions

    Args:
        workflow_id: UUID workflow
        db: Database session
        current_user: Authenticated user

    Returns:
        Lista WorkflowExecutionResponse (sorted by started_at desc)

    Raises:
        404: Jeśli workflow nie istnieje lub user nie ma dostępu

    Example:
        GET /api/v1/workflows/{uuid}/executions
    """
    logger.debug(
        f"Fetching execution history for workflow {workflow_id}",
        extra={"user_id": str(current_user.id), "workflow_id": str(workflow_id)},
    )

    # Auth check (workflow exists + user has access)
    service = WorkflowService(db)
    try:
        await service.get_workflow_by_id(workflow_id, current_user.id)
    except HTTPException:
        # Re-raise 404
        raise

    # Get executions
    stmt = (
        select(WorkflowExecution)
        .where(WorkflowExecution.workflow_id == workflow_id)
        .order_by(WorkflowExecution.started_at.desc())
    )

    result = await db.execute(stmt)
    executions = result.scalars().all()

    logger.info(
        f"Found {len(executions)} executions for workflow {workflow_id}",
        extra={
            "workflow_id": str(workflow_id),
            "executions_count": len(executions),
            "user_id": str(current_user.id),
        },
    )

    return list(executions)
