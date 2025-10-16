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
"""

from .persona_generator_langchain import (
    PersonaGeneratorLangChain as PersonaGenerator,
    DemographicDistribution,
)
from .memory_service_langchain import MemoryServiceLangChain as MemoryService
from .focus_group_service_langchain import FocusGroupServiceLangChain as FocusGroupService
from .discussion_summarizer import DiscussionSummarizerService
from .survey_response_generator import SurveyResponseGenerator
from .persona_needs_service import PersonaNeedsService
from .persona_messaging_service import PersonaMessagingService
from .persona_comparison_service import PersonaComparisonService

__all__ = [
    "PersonaGenerator",
    "DemographicDistribution",
    "MemoryService",
    "FocusGroupService",
    "DiscussionSummarizerService",
    "SurveyResponseGenerator",
    "PersonaNeedsService",
    "PersonaMessagingService",
    "PersonaComparisonService",
]
