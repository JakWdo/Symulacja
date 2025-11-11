"""
API endpoints dla Workflow Builder - Compatibility Wrapper

UWAGA: Ten plik jest cienkim wrapperem dla kompatybilności wstecznej.
Rzeczywista implementacja znajduje się w:
- workflow_crud.py - CRUD operations (6 endpoints)
- workflow_execution.py - Validation & execution (3 endpoints)
- workflow_templates.py - Templates (2 endpoints)

Total endpoints: 11 (przez include z 3 modułów)

Ten router łączy wszystkie 3 moduły w jeden dla kompatybilności z istniejącym kodem.
"""

from fastapi import APIRouter
from app.api import workflow_crud, workflow_execution, workflow_templates

# Główny router (agreguje wszystkie workflow endpoints)
router = APIRouter(prefix="/workflows", tags=["Workflows"])

# Include routerów z poszczególnych modułów
router.include_router(workflow_crud.router, prefix="", tags=["Workflows"])
router.include_router(workflow_execution.router, prefix="", tags=["Workflows"])
router.include_router(workflow_templates.router, prefix="/templates", tags=["Workflows"])
