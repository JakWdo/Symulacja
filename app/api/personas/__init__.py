"""
Personas API Module

Modularny endpoint dla zarządzania personami.

Structure:
- utils.py: 36 utility functions (polishification, segment building, etc.)
- generation.py: POST /generate endpoint (~700 lines)
- crud.py: GET /, GET /{id}, DELETE /{id} (~400 lines)
- details.py: GET /details/{id}, POST /export/{id} (~300 lines)
- actions.py: POST /comparison + archived messaging (~200 lines)
- reasoning.py: GET /reasoning/{id} (~200 lines)

Router agreguje wszystkie sub-routers w jeden główny router.
"""

from fastapi import APIRouter

from .generation import router as generation_router
from .crud import router as crud_router
from .details import router as details_router
from .actions import router as actions_router
from .reasoning import router as reasoning_router

# Główny router agregujący wszystkie endpointy
router = APIRouter()

# Include sub-routers (zachowaj kolejność dla czytelności)
router.include_router(generation_router, tags=["Personas"])
router.include_router(crud_router, tags=["Personas"])
router.include_router(details_router, tags=["Personas"])
router.include_router(actions_router, tags=["Personas"])
router.include_router(reasoning_router, tags=["Personas"])

__all__ = ["router"]
