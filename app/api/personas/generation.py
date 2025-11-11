"""
Persona API - Generation Module (Backward Compatibility Wrapper)

UWAGA: Ten plik jest cienko opakowaniem dla backward compatibility.
Rzeczywista implementacja została podzielona na 3 moduły:

- generation_endpoints.py: Router, endpointy API, helper functions
- orchestration_endpoints.py: SSE streaming helpers
- validation_endpoints.py: Background worker z walidacją

Importuj z nowych modułów zamiast tego pliku w nowym kodzie.
"""

# Re-export wszystkich funkcji dla backward compatibility
from .generation_endpoints import (
    router,
    limiter,
    logger,
    _infer_full_name,
    _fallback_full_name,
    _extract_age_from_story,
    _get_consistent_occupation,
    _fallback_polish_list,
    generate_personas,
    generate_personas_stream,
)

from .validation_endpoints import (
    _running_tasks,
    _generate_personas_task,
)

from .orchestration_endpoints import (
    _generate_personas_task_streaming,
    _generate_personas_task_with_progress,
)

__all__ = [
    "router",
    "limiter",
    "logger",
    "_infer_full_name",
    "_fallback_full_name",
    "_extract_age_from_story",
    "_get_consistent_occupation",
    "_fallback_polish_list",
    "generate_personas",
    "generate_personas_stream",
    "_running_tasks",
    "_generate_personas_task",
    "_generate_personas_task_streaming",
    "_generate_personas_task_with_progress",
]
