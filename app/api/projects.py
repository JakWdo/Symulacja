"""
Backward Compatibility Wrapper dla Projects API

Ten moduł zachowuje kompatybilność wsteczną dla kodu importującego `app.api.projects`.
Faktyczne endpointy zostały przeniesione do:
- project_crud.py - podstawowe operacje CRUD
- project_demographics.py - soft delete operations i archiwizacja

Ten wrapper re-eksportuje routery z nowych modułów.
"""
from fastapi import APIRouter
from app.api.project_crud import router as crud_router
from app.api.project_demographics import router as demographics_router

# Utwórz router agregujący oba moduły dla kompatybilności
router = APIRouter()
router.include_router(crud_router)
router.include_router(demographics_router)
