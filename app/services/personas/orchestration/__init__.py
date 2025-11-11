"""Orchestration submodule dla persona generation.

Ten pakiet zawiera helper functions i models używane przez PersonaOrchestrationService:

Modules:
- models: Pydantic models (GraphInsight, DemographicGroup, PersonaAllocationPlan)
- graph_context_fetcher: Pobieranie Graph RAG context z hybrid search
- prompt_builder: Długi edukacyjny prompt dla Gemini 2.5 Pro
- json_parser: 4-strategy JSON extraction z LLM responses
- segment_naming: Generacja mówiących nazw segmentów (Gemini Flash)
- segment_context_generator: Generacja długich briefów (Gemini 2.5 Pro)
- filtering_utils: Filtrowanie insights i citations per segment
"""

from .models import (
    GraphInsight,
    DemographicGroup,
    PersonaAllocationPlan,
    map_graph_node_to_insight
)
from .graph_context_fetcher import (
    get_comprehensive_graph_context,
    _format_graph_context
)
from .prompt_builder import build_orchestration_prompt
from .json_parser import extract_json_from_response
from .segment_naming import generate_segment_name
from .segment_context_generator import generate_segment_context
from .filtering_utils import (
    filter_graph_insights_for_segment,
    filter_rag_citations
)

__all__ = [
    # Models
    "GraphInsight",
    "DemographicGroup",
    "PersonaAllocationPlan",
    "map_graph_node_to_insight",
    # Graph RAG
    "get_comprehensive_graph_context",
    # Prompt
    "build_orchestration_prompt",
    # JSON parsing
    "extract_json_from_response",
    # Segment generation
    "generate_segment_name",
    "generate_segment_context",
    # Filtering
    "filter_graph_insights_for_segment",
    "filter_rag_citations",
]
