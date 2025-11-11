"""
Serwis pre-built workflow templates

UWAGA: To jest cienki wrapper dla zachowania kompatybilności wstecznej.
Główna logika została przeniesiona do:
- template_crud.py - operacje CRUD i TEMPLATES dict
- template_validator.py - walidacja templates

Po zaktualizowaniu wszystkich importów w projekcie, ten plik może być usunięty.
"""

# Re-export z template_crud dla kompatybilności wstecznej
from .template_crud import WorkflowTemplateCRUD as WorkflowTemplateService

__all__ = ["WorkflowTemplateService"]
