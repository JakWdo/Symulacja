"""
API endpoints dla Workflow Builder

Ten moduł zawiera wszystkie endpoints do zarządzania workflow:
- CRUD operations (create, list, get, update, delete)
- Canvas quick save (PATCH /canvas)
- Validation (POST /validate)
- Execution (POST /execute)
- Execution history (GET /executions)
- Templates (GET /templates, POST /templates/{id}/instantiate)

Total endpoints: 11

Konwencje:
- Wszystkie response models używają Pydantic schemas z app/schemas/workflow.py
- Auth wymagany dla wszystkich endpoints (Depends(get_current_user))
- Error handling z proper HTTP status codes (200, 201, 400, 404, 500)
- Polish docstrings
- Logging dla wszystkich operations
"""

import logging
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.dependencies import get_current_user, get_current_user_optional
from app.models import User, WorkflowExecution
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowExecuteRequest,
    WorkflowExecutionResponse,
    ValidationResult,
    WorkflowTemplateResponse,
    WorkflowInstantiateRequest,
    CanvasData,
)
from app.services.workflows import (
    WorkflowService,
    WorkflowValidator,
    WorkflowExecutor,
    WorkflowTemplateService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflows", tags=["Workflows"])


# ==================== CRUD OPERATIONS ====================


@router.post("/", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    data: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Tworzy nowy workflow.

    Workflow to graf nodes i edges (React Flow canvas) z business logic.
    Każdy workflow należy do projektu i ma właściciela.

    Args:
        data: Dane workflow (name, project_id, description, canvas_data)
        db: Database session
        current_user: Authenticated user

    Returns:
        WorkflowResponse z utworzonym workflow

    Raises:
        404: Jeśli project nie istnieje
        403: Jeśli user nie ma dostępu do projektu
        400: Jeśli canvas_data invalid

    Example:
        POST /api/v1/workflows/
        {
          "name": "Product Research Flow",
          "project_id": "uuid-projektu",
          "description": "Badanie funkcji produktu",
          "canvas_data": {"nodes": [], "edges": []}
        }
    """
    logger.info(
        f"Creating workflow '{data.name}' for project {data.project_id}",
        extra={"user_id": str(current_user.id), "project_id": str(data.project_id)},
    )

    service = WorkflowService(db)

    try:
        workflow = await service.create_workflow(data, current_user.id)

        logger.info(
            "Workflow created successfully",
            extra={
                "workflow_id": str(workflow.id),
                "workflow_name": workflow.name,
                "user_id": str(current_user.id),
            },
        )

        return workflow

    except ValueError as e:
        # Validation error (project not found, access denied, etc.)
        logger.warning(
            f"Workflow creation failed: {e}",
            extra={"user_id": str(current_user.id), "project_id": str(data.project_id)},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        # Unexpected error
        logger.error(
            f"Workflow creation error: {e}",
            exc_info=True,
            extra={"user_id": str(current_user.id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create workflow",
        )


@router.get("/", response_model=list[WorkflowResponse])
async def list_workflows(
    project_id: UUID | None = None,
    include_templates: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lista workflows użytkownika.

    Query params:
    - project_id: Filter workflows po projekcie (optional)
    - include_templates: Czy dołączyć system templates (default: False)

    Args:
        project_id: UUID projektu (optional filter)
        include_templates: Czy dołączyć templates
        db: Database session
        current_user: Authenticated user

    Returns:
        Lista WorkflowResponse (sorted by created_at desc)

    Example:
        GET /api/v1/workflows/?project_id=uuid-projektu&include_templates=false
    """
    logger.debug(
        "Listing workflows",
        extra={
            "user_id": str(current_user.id),
            "project_id": str(project_id) if project_id else None,
            "include_templates": include_templates,
        },
    )

    service = WorkflowService(db)

    if project_id:
        workflows = await service.list_workflows_by_project(
            project_id, current_user.id, include_templates
        )
    else:
        # List ALL workflows dla user (wszystkie projekty)
        workflows = await service.list_workflows_by_user(
            current_user.id, include_templates
        )

    logger.info(
        f"Found {len(workflows)} workflows",
        extra={"user_id": str(current_user.id), "count": len(workflows)},
    )

    return workflows


# ==================== TEMPLATES ====================


@router.get("/templates", response_model=list[WorkflowTemplateResponse])
async def get_templates(
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Pobiera listę workflow templates.

    Templates to pre-built workflows które user może customize.
    MVP templates:
    - basic_research: 4-step quick research (personas + survey + analysis)
    - deep_dive: 6-step comprehensive (personas + focus group + survey + analysis + export)
    - validation_flow: 5-step product validation

    Returns:
        Lista WorkflowTemplateResponse (sorted by estimated_time_minutes)

    Example:
        GET /api/v1/workflows/templates

    Response:
        [
          {
            "id": "basic_research",
            "name": "Basic Research Flow",
            "description": "Quick 4-step flow for rapid insights",
            "category": "research",
            "node_count": 4,
            "estimated_time_minutes": 3,
            "canvas_data": {...},
            "tags": ["quick", "personas", "survey"]
          }
        ]
    """
    user_id = str(current_user.id) if current_user else "anonymous"
    logger.debug("Fetching workflow templates", extra={"user_id": user_id})

    service = WorkflowTemplateService()
    templates = service.get_templates()

    # Sort by time (fastest first)
    templates_sorted = sorted(
        templates, key=lambda t: t.estimated_time_minutes or 0
    )

    logger.info(
        f"Returning {len(templates_sorted)} workflow templates",
        extra={"templates_count": len(templates_sorted)},
    )

    return templates_sorted


@router.post(
    "/templates/{template_id}/instantiate",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
)
async def instantiate_template(
    template_id: str,
    request: WorkflowInstantiateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Tworzy workflow z template.

    User wybiera template i tworzy nowy workflow na jego podstawie.
    Canvas zostaje skopiowany, user może go później edytować.

    Args:
        template_id: ID template (np. "basic_research", "deep_dive")
        request: Request body z project_id i workflow_name
        db: Database session
        current_user: Authenticated user

    Returns:
        WorkflowResponse z utworzonym workflow

    Raises:
        404: Jeśli template nie istnieje
        400: Jeśli project nie istnieje lub user nie ma dostępu

    Example:
        POST /api/v1/workflows/templates/basic_research/instantiate
        {
          "project_id": "uuid-projektu",
          "workflow_name": "My Product Research"
        }
    """
    logger.info(
        f"Instantiating template '{template_id}' for project {request.project_id}",
        extra={
            "user_id": str(current_user.id),
            "template_id": template_id,
            "project_id": str(request.project_id),
        },
    )

    service = WorkflowTemplateService()

    try:
        workflow = await service.create_from_template(
            template_id=template_id,
            project_id=request.project_id,
            user_id=current_user.id,
            workflow_name=request.workflow_name,
            db=db,
        )

        logger.info(
            "Workflow created from template successfully",
            extra={
                "workflow_id": str(workflow.id),
                "workflow_name": workflow.name,
                "template_id": template_id,
                "user_id": str(current_user.id),
            },
        )

        return workflow

    except ValueError as e:
        # Template not found or validation error
        logger.warning(
            f"Template instantiation failed: {e}",
            extra={
                "template_id": template_id,
                "project_id": str(request.project_id),
                "user_id": str(current_user.id),
            },
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except HTTPException:
        # Re-raise HTTPException (403, etc.)
        raise

    except Exception as e:
        logger.error(
            f"Template instantiation error: {e}",
            exc_info=True,
            extra={
                "template_id": template_id,
                "project_id": str(request.project_id),
                "user_id": str(current_user.id),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create workflow from template",
        )


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pobiera workflow po ID.

    Args:
        workflow_id: UUID workflow
        db: Database session
        current_user: Authenticated user

    Returns:
        WorkflowResponse z pełnymi danymi workflow

    Raises:
        404: Jeśli workflow nie istnieje lub user nie ma dostępu

    Example:
        GET /api/v1/workflows/{uuid}
    """
    logger.debug(
        f"Fetching workflow {workflow_id}",
        extra={"user_id": str(current_user.id), "workflow_id": str(workflow_id)},
    )

    service = WorkflowService(db)

    try:
        workflow = await service.get_workflow_by_id(workflow_id, current_user.id)
        return workflow

    except HTTPException:
        # Re-raise HTTPException (404)
        raise

    except Exception as e:
        logger.error(
            f"Error fetching workflow: {e}",
            exc_info=True,
            extra={"workflow_id": str(workflow_id), "user_id": str(current_user.id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch workflow",
        )


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: UUID,
    data: WorkflowUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Aktualizuje workflow (partial update).

    Można aktualizować:
    - name: Nazwa workflow
    - description: Opis
    - canvas_data: Stan canvas (nodes/edges)
    - status: Status (draft/active/archived)

    Args:
        workflow_id: UUID workflow
        data: Dane do aktualizacji (tylko podane pola będą zmienione)
        db: Database session
        current_user: Authenticated user

    Returns:
        Zaktualizowany WorkflowResponse

    Raises:
        404: Jeśli workflow nie istnieje
        400: Jeśli workflow jest template (read-only)
        403: Jeśli user nie ma dostępu

    Example:
        PUT /api/v1/workflows/{uuid}
        {
          "name": "Product Research Flow v2",
          "canvas_data": {"nodes": [...], "edges": [...]}
        }
    """
    logger.info(
        f"Updating workflow {workflow_id}",
        extra={"user_id": str(current_user.id), "workflow_id": str(workflow_id)},
    )

    service = WorkflowService(db)

    try:
        workflow = await service.update_workflow(workflow_id, data, current_user.id)

        logger.info(
            "Workflow updated successfully",
            extra={
                "workflow_id": str(workflow_id),
                "workflow_name": workflow.name,
                "user_id": str(current_user.id),
            },
        )

        return workflow

    except ValueError as e:
        # Validation error (template update, etc.)
        logger.warning(
            f"Workflow update failed: {e}",
            extra={"workflow_id": str(workflow_id), "user_id": str(current_user.id)},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except HTTPException:
        # Re-raise HTTPException (404)
        raise

    except Exception as e:
        logger.error(
            f"Workflow update error: {e}",
            exc_info=True,
            extra={"workflow_id": str(workflow_id), "user_id": str(current_user.id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update workflow",
        )


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft delete workflow.

    Workflow zostanie oznaczony jako usunięty (deleted_at).
    Hard delete nastąpi po 7 dniach (cleanup job).

    Args:
        workflow_id: UUID workflow
        db: Database session
        current_user: Authenticated user

    Returns:
        Success message

    Raises:
        404: Jeśli workflow nie istnieje
        403: Jeśli user nie ma dostępu

    Example:
        DELETE /api/v1/workflows/{uuid}
    """
    logger.info(
        f"Deleting workflow {workflow_id}",
        extra={"user_id": str(current_user.id), "workflow_id": str(workflow_id)},
    )

    service = WorkflowService(db)

    try:
        await service.soft_delete_workflow(workflow_id, current_user.id)

        logger.info(
            "Workflow deleted successfully",
            extra={"workflow_id": str(workflow_id), "user_id": str(current_user.id)},
        )

        return {"message": "Workflow deleted successfully"}

    except HTTPException:
        # Re-raise HTTPException (404, 403)
        raise

    except Exception as e:
        logger.error(
            f"Workflow deletion error: {e}",
            exc_info=True,
            extra={"workflow_id": str(workflow_id), "user_id": str(current_user.id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete workflow",
        )


@router.patch("/{workflow_id}/canvas", response_model=WorkflowResponse)
async def quick_save_canvas(
    workflow_id: UUID,
    canvas_data: CanvasData = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Quick save dla canvas state (optimizacja auto-save).

    Endpoint zoptymalizowany pod częste auto-save z frontend.
    Aktualizuje TYLKO canvas_data, nic więcej.

    Args:
        workflow_id: UUID workflow
        canvas_data: Canvas state {nodes: [], edges: []}
        db: Database session
        current_user: Authenticated user

    Returns:
        Zaktualizowany WorkflowResponse

    Raises:
        404: Jeśli workflow nie istnieje
        400: Jeśli canvas_data invalid

    Example:
        PATCH /api/v1/workflows/{uuid}/canvas
        {
          "canvas_data": {
            "nodes": [{...}],
            "edges": [{...}]
          }
        }
    """
    logger.debug(
        f"Quick save canvas for workflow {workflow_id}",
        extra={"user_id": str(current_user.id), "workflow_id": str(workflow_id)},
    )

    service = WorkflowService(db)

    try:
        workflow = await service.save_canvas_state(
            workflow_id, canvas_data.model_dump(), current_user.id
        )

        logger.debug(
            "Canvas saved successfully",
            extra={"workflow_id": str(workflow_id), "user_id": str(current_user.id)},
        )

        return workflow

    except ValueError as e:
        # Validation error (invalid canvas_data)
        logger.warning(
            f"Canvas save failed: {e}",
            extra={"workflow_id": str(workflow_id), "user_id": str(current_user.id)},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except HTTPException:
        # Re-raise HTTPException (404)
        raise

    except Exception as e:
        logger.error(
            f"Canvas save error: {e}",
            exc_info=True,
            extra={"workflow_id": str(workflow_id), "user_id": str(current_user.id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save canvas state",
        )


# ==================== VALIDATION & EXECUTION ====================


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

