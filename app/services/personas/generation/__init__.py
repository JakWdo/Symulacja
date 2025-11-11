"""
Persona Generation Module

Moduły odpowiedzialne za generowanie person:
- PersonaGeneratorLangChain - Główny generator person z RAG
- SegmentConstructor - Konstrukcja segmentów demograficznych
- DemographicDistribution - Model dystrybucji demograficznej
- PersonaNeedsService - Generowanie Jobs-to-be-Done i pain points
"""

from .persona_generator_langchain import PersonaGeneratorLangChain
from .segment_constructor import SegmentConstructor
from .demographic_sampling import DemographicDistribution
from .persona_needs_service import PersonaNeedsService
from .prompt_templates import get_persona_prompt_template
from .rag_integration import get_rag_context_for_persona
from .psychological_profiles import sample_big_five_traits, sample_cultural_dimensions

__all__ = [
    "PersonaGeneratorLangChain",
    "SegmentConstructor",
    "DemographicDistribution",
    "PersonaNeedsService",
    "get_persona_prompt_template",
    "get_rag_context_for_persona",
    "sample_big_five_traits",
    "sample_cultural_dimensions",
]
