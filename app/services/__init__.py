"""
Services module - organized by functional domain.

Structure (REORGANIZED 2025-10-20):
- shared/       - Shared utilities and LLM clients
- personas/     - Persona management services
- focus_groups/ - Focus group and discussion services
- rag/          - RAG and knowledge graph services
- surveys/      - Survey services
- archived/     - Legacy/archived services

All services are re-exported from this module for backward compatibility.

Main services:
- PersonaGenerator: Generuje realistyczne persony z AI (Gemini Flash + RAG)
- FocusGroupService: Orkiestruje dyskusje grup fokusowych
- MemoryService: Event sourcing + semantic search
- DiscussionSummarizerService: AI-powered podsumowania
- RAG services: Document management, Graph RAG, Hybrid Search

Architektura: Service Layer Pattern (API → Services → Models)
Framework: LangChain + Google Gemini (Flash dla szybkości, Pro dla analiz)
"""

# Shared utilities
from .shared import build_chat_model

# Persona services (with backward-compatible aliases)
from .personas import (
    PersonaGeneratorLangChain,
    PersonaOrchestrationService,
    PersonaValidator,
    PersonaDetailsService,
    PersonaNeedsService,
    PersonaAuditService,
    SegmentBriefService,
)

# Focus group services (with backward-compatible aliases)
from .focus_groups import (
    FocusGroupServiceLangChain,
    DiscussionSummarizerService,
    MemoryServiceLangChain,
)

# RAG services
from .rag import (
    RAGDocumentService,
    GraphRAGService,
    PolishSocietyRAG,
    get_graph_store,
    get_vector_store,
)

# Survey services
from .surveys import (
    SurveyResponseGenerator,
)

# Backward-compatible aliases (DEPRECATED - use full names instead)
PersonaGenerator = PersonaGeneratorLangChain
MemoryService = MemoryServiceLangChain
FocusGroupService = FocusGroupServiceLangChain

__all__ = [
    # Shared
    "build_chat_model",
    # Personas
    "PersonaGeneratorLangChain",
    "PersonaOrchestrationService",
    "PersonaValidator",
    "PersonaDetailsService",
    "PersonaNeedsService",
    "PersonaAuditService",
    "SegmentBriefService",
    # Focus groups
    "FocusGroupServiceLangChain",
    "DiscussionSummarizerService",
    "MemoryServiceLangChain",
    # RAG
    "RAGDocumentService",
    "GraphRAGService",
    "PolishSocietyRAG",
    "get_graph_store",
    "get_vector_store",
    # Surveys
    "SurveyResponseGenerator",
    # Backward-compatible aliases (DEPRECATED)
    "PersonaGenerator",
    "MemoryService",
    "FocusGroupService",
]
