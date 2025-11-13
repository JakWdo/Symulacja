"""
API endpoints dla Workflow Builder - Template Operations

Ten moduł zawiera endpointy dla workflow templates:
- GET /templates - Get available templates
- POST /templates/{template_id}/instantiate - Create workflow from template

Total endpoints: 2

Konwencje:
- Wszystkie response models używają Pydantic schemas z app/schemas/workflow.py
- Auth wymagany dla instantiate (get_templates może być anonymous)
- Error handling z proper HTTP status codes (200, 201, 404, 422, 500)
- Polish docstrings
- Logging dla wszystkich operations
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.dependencies import get_current_user, get_current_user_optional
from app.models import User
from app.schemas.workflow import (
    WorkflowResponse,
    WorkflowTemplateResponse,
    WorkflowInstantiateRequest,
)
from app.services.workflows import WorkflowTemplateService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Workflows"])


@router.get("/", response_model=list[WorkflowTemplateResponse])
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
    "/{template_id}/instantiate",
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
    # Debug logging - format przyjazny dla GCP (textPayload)
    logger.info(
        f"Instantiating template '{template_id}' for user {current_user.id}\n"
        f"Request data:\n"
        f"  - project_id: {request.project_id} (type: {type(request.project_id).__name__})\n"
        f"  - workflow_name: {request.workflow_name}\n"
        f"  - template_id: {template_id}"
    )

    # Explicit validation dla lepszych error messages
    if not request.project_id:
        logger.warning(
            "Missing project_id for template instantiation",
            extra={
                "template_id": template_id,
                "user_id": str(current_user.id),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "project_id is required",
                "field": "project_id",
                "hint": "Please provide a valid project UUID",
            },
        )

    import uuid

    service = WorkflowTemplateService()
    error_id = str(uuid.uuid4())[:8]

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
            f"[{error_id}] Template instantiation failed: {e}",
            extra={
                "error_id": error_id,
                "template_id": template_id,
                "project_id": str(request.project_id),
                "user_id": str(current_user.id),
            },
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{str(e)} (error_id: {error_id})"
        )

    except HTTPException as http_ex:
        # Re-raise HTTPException with preserved detail (404, 403, etc.)
        # WorkflowService now returns structured error details
        logger.warning(
            f"[{error_id}] Template instantiation HTTP error: {http_ex.status_code}",
            extra={
                "error_id": error_id,
                "template_id": template_id,
                "project_id": str(request.project_id),
                "user_id": str(current_user.id),
                "status_code": http_ex.status_code,
                "detail": http_ex.detail
            },
        )
        await db.rollback()
        raise

    except Exception as e:
        logger.error(
            f"[{error_id}] Template instantiation unexpected error: {e}",
            exc_info=True,
            extra={
                "error_id": error_id,
                "template_id": template_id,
                "project_id": str(request.project_id),
                "user_id": str(current_user.id),
                "error_type": type(e).__name__,
                "alert": True
            },
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "Failed to create workflow from template",
                "error_id": error_id,
                "hint": "Please check server logs for details or contact support"
            },
        )
