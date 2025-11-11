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

from .persona_generator_langchain import PersonaGeneratorLangChain
from .persona_orchestration import PersonaOrchestrationService
from .persona_validator import PersonaValidator
from .persona_details_service import PersonaDetailsService
from .persona_needs_service import PersonaNeedsService
from .persona_audit_service import PersonaAuditService
from .segment_brief_service import SegmentBriefService

# Re-export z orchestration submodule (dla backward compatibility)
from .orchestration import (
    GraphInsight,
    DemographicGroup,
    PersonaAllocationPlan,
)

# Re-export z nowych modułów pomocniczych (dla backward compatibility)
from .demographic_sampling import DemographicDistribution
from .psychological_profiles import sample_big_five_traits, sample_cultural_dimensions
from .statistical_validation import validate_distribution
from .rag_integration import get_rag_context_for_persona

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
