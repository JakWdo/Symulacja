"""
Persona API Module

This module aggregates all persona-related API endpoints from submodules:
- crud: CRUD operations (list, summary, delete, undo, bulk-delete)
- generation_endpoints: Persona generation endpoints (split from generation.py)
- orchestration_endpoints: SSE streaming helpers for generation progress
- validation_endpoints: Background task for persona generation with validation
- details: Detail/read operations (reasoning, details, archived)
- helpers: Shared utility functions

The main router combines all sub-routers for clean organization.
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .generation_endpoints import router as generation_router
from .details import router as details_router


# Main router that aggregates all persona endpoints
router = APIRouter()

# Include sub-routers
router.include_router(crud_router, tags=["personas"])
router.include_router(generation_router, tags=["personas"])
router.include_router(details_router, tags=["personas"])


__all__ = ["router"]
