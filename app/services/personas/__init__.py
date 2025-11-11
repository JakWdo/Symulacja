"""
Persona management services.

Serwisy odpowiedzialne za generowanie, walidację i zarządzanie personami:
- PersonaGeneratorLangChain - Generowanie person z RAG
- PersonaOrchestrationService - Orkiestracja alokacji person do segmentów
- PersonaValidatorService - Walidacja person
- PersonaDetailsService - Orchestrator dla Persona Detail View
- PersonaNeedsService - Generowanie JTBD i pain points
- PersonaAuditService - Audit log dla person
- SegmentBriefService - Generowanie briefów segmentów (NEW)
"""

# Import głównych serwisów z podmodułów
from .generation import PersonaGeneratorLangChain, PersonaNeedsService
from .orchestration import PersonaOrchestrationService, SegmentBriefService
from .validation import PersonaValidator, PersonaAuditService
from .details import PersonaDetailsService

# Re-export z orchestration submodule (dla backward compatibility)
from .orchestration import (
    GraphInsight,
    DemographicGroup,
    PersonaAllocationPlan,
)

# Re-export z nowych modułów pomocniczych (dla backward compatibility)
from .generation import (
    DemographicDistribution,
    sample_big_five_traits,
    sample_cultural_dimensions,
    get_rag_context_for_persona,
)
from .validation import validate_distribution

__all__ = [
    "PersonaGeneratorLangChain",
    "PersonaOrchestrationService",
    "PersonaValidator",
    "PersonaDetailsService",
    "PersonaNeedsService",
    "PersonaAuditService",
    "SegmentBriefService",
    # Orchestration models
    "GraphInsight",
    "DemographicGroup",
    "PersonaAllocationPlan",
    # Helper modules exports
    "DemographicDistribution",
    "sample_big_five_traits",
    "sample_cultural_dimensions",
    "validate_distribution",
    "get_rag_context_for_persona",
]
