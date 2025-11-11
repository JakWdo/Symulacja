"""
API endpoints dla Workflow Builder - CRUD Operations

Ten moduł zawiera endpointy CRUD dla workflow:
- POST / - Create workflow
- GET / - List workflows (z filtrowaniem po project_id)
- GET /{workflow_id} - Get workflow by ID
- PUT /{workflow_id} - Update workflow
- DELETE /{workflow_id} - Soft delete workflow
- PATCH /{workflow_id}/canvas - Quick save canvas state

Total endpoints: 6

Konwencje:
- Wszystkie response models używają Pydantic schemas z app/schemas/workflow.py
- Auth wymagany dla wszystkich endpoints (Depends(get_current_user))
- Error handling z proper HTTP status codes (200, 201, 400, 404, 500)
- Polish docstrings
- Logging dla wszystkich operations
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.dependencies import get_current_user
from app.models import User
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    CanvasData,
)
from app.services.workflows import WorkflowService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Workflows"])


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
