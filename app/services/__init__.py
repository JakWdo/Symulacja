"""
Moduł Services - Logika Biznesowa

Zawiera serwisy implementujące główną funkcjonalność platformy:

- PersonaGenerator: Generuje realistyczne persony z AI (Gemini Flash)
  * Sampling demografii z rozkładów prawdopodobieństwa
  * Sampling cech osobowości (Big Five, Hofstede)
  * Walidacja statystyczna (chi-kwadrat)
  * ~1.5-3s na personę

- FocusGroupService: Orkiestruje dyskusje grup fokusowych
  * Równoległe przetwarzanie odpowiedzi person (asyncio)
  * Integracja z MemoryService dla kontekstu
  * Target: <3s per persona, <30s całkowity czas

- MemoryService: Event sourcing + semantic search
  * Przechowuje historię działań person (PersonaEvent)
  * Embeddingi (Google Gemini) dla similarity search
  * Temporal decay - nowsze eventy mają większą wagę

- DiscussionSummarizerService: AI-powered podsumowania
  * Sentiment analysis
  * Idea Score (0-100)
  * Consensus level
  * Executive summary (Gemini Pro/Flash)

- SurveyResponseGenerator: Generuje odpowiedzi na ankiety
  * 4 typy pytań: single/multiple choice, rating scale, open text
  * Persony odpowiadają zgodnie z demografią i osobowością

Architektura: Service Layer Pattern (API → Services → Models)
Framework: LangChain + Google Gemini (Flash dla szybkości, Pro dla analiz)

Struktura folderów:
- personas/: Serwisy związane z generacją i zarządzaniem personami
- rag/: System RAG (document management, hybrid search, graph RAG)
- focus_groups/: Focus groups, dyskusje, memory, surveys
- core/: Współdzielone utility services
- archived/: Legacy features (nie używane w obecnej wersji)
"""

# Personas
from .personas import (
    PersonaGeneratorLangChain as PersonaGenerator,
    PersonaOrchestrationService,
    PersonaValidator,
    PersonaDetailsService,
    PersonaNarrativeService,
    PersonaAuditService,
    PersonaComparisonService,
    PersonaNeedsService,
    PersonaMessagingService,
)

# RAG
from .rag import (
    RAGDocumentService,
    GraphRAGService,
    PolishSocietyRAG,
    GraphContextProvider,
    HybridContextProvider,
    get_vector_store,
    get_graph_store,
)

# Focus Groups
from .focus_groups import (
    FocusGroupServiceLangChain as FocusGroupService,
    DiscussionSummarizerService,
    MemoryServiceLangChain as MemoryService,
    SurveyResponseGenerator,
)

# Core
from .core import build_chat_model, get_embeddings

# Legacy exports for backwards compatibility
# TODO: Remove these aliases once all imports are updated
from .personas.persona_generator_langchain import DemographicDistribution

# Utrzymaj kompatybilność ścieżek importu z poprzednich wersji pakietu
import sys
from .rag import rag_hybrid_search_service as _rag_hybrid_search_service

sys.modules.setdefault("app.services.rag_hybrid_search_service", _rag_hybrid_search_service)

__all__ = [
    # Personas
    "PersonaGenerator",
    "PersonaOrchestrationService",
    "PersonaValidator",
    "PersonaDetailsService",
    "PersonaNarrativeService",
    "PersonaAuditService",
    "PersonaComparisonService",
    "PersonaNeedsService",
    "PersonaMessagingService",
    "DemographicDistribution",
    # RAG
    "RAGDocumentService",
    "GraphRAGService",
    "PolishSocietyRAG",
    "GraphContextProvider",
    "HybridContextProvider",
    "get_vector_store",
    "get_graph_store",
    # Focus Groups
    "FocusGroupService",
    "DiscussionSummarizerService",
    "MemoryService",
    "SurveyResponseGenerator",
    # Core
    "build_chat_model",
    "get_embeddings",
]
