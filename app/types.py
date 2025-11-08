"""
Wspólne type aliases dla całej aplikacji Sight.

Centralizuje często używane typy aby poprawić type safety i czytelność kodu.
Używaj tych aliasów zamiast generycznych Dict[str, Any] wszędzie gdzie to możliwe.
"""
from typing import Union, Literal
from uuid import UUID
from datetime import datetime

# ============================================================================
# JSON-like Types (zastępnik Dict[str, Any] dla JSON data)
# ============================================================================
# UWAGA: Użycie Any dla rekurencyjnych typów JSON jest akceptowalne
# ponieważ JSON jest inherentnie dynamicznie typowany

from typing import Any as _JSONAny

JSONPrimitive = Union[str, int, float, bool, None]
"""Prymitywne typy JSON: string, number, boolean, null"""

JSONValue = Union[JSONPrimitive, list[_JSONAny], dict[str, _JSONAny]]
"""
Wartość JSON - może być prymitywem, listą lub dictem.
Używa Any dla nested structures aby uniknąć infinite recursion w Pydantic.
"""

JSONObject = dict[str, _JSONAny]
"""JSON object - dict z string keys i dowolnymi wartościami"""

JSONArray = list[_JSONAny]
"""JSON array - lista dowolnych wartości"""

# ============================================================================
# Entity ID Types
# ============================================================================

EntityID = Union[str, UUID]
"""ID encji - może być string lub UUID"""

Timestamp = datetime
"""Timestamp - datetime object"""

# ============================================================================
# Survey Types
# ============================================================================

QuestionType = Literal["single-choice", "multiple-choice", "rating-scale", "open-text"]
"""Typy pytań ankietowych"""

AnswerValue = Union[int, str, list[str]]
"""
Wartość odpowiedzi na pytanie ankietowe:
- int: rating-scale (1-5, 1-10, etc.)
- str: single-choice lub open-text
- list[str]: multiple-choice
"""

AnswerDict = dict[str, AnswerValue]
"""Dict z odpowiedziami: question_id -> answer_value"""

QuestionDict = dict[str, Union[str, list[str], int]]
"""
Struktura pytania ankietowego z bazy:
- id: str
- type: QuestionType
- title: str
- description: str (optional)
- options: list[str] (dla choice questions)
- scaleMin: int (dla rating-scale)
- scaleMax: int (dla rating-scale)
"""

QuestionStatistics = dict[str, Union[int, float, str, list[str], dict[str, int]]]
"""
Statystyki dla pytania:
- single/multiple-choice: distribution (dict), most_common
- rating-scale: mean, median, mode, min, max, std, distribution
- open-text: total_responses, avg_word_count, sample_responses
"""

# ============================================================================
# LLM Response Types
# ============================================================================

LLMResponse = str
"""Odpowiedź z LLM - zawsze string (content z AIMessage)"""

LLMMessages = list[tuple[str, str]]
"""Lista wiadomości LLM: [(role, content), ...]"""

# ============================================================================
# RAG Types
# ============================================================================

RAGCitation = dict[str, Union[str, float, int]]
"""
Cytowanie z RAG:
- source: str (nazwa dokumentu)
- excerpt: str (fragment tekstu)
- relevance_score: float (0-1)
- chunk_id: str (UUID chunka)
"""

RAGContextDetails = dict[str, Union[str, list[RAGCitation], JSONObject]]
"""
Szczegóły kontekstu RAG:
- orchestration_reasoning: dict (orchestration brief)
- graph_insights: list[dict] (węzły Neo4j)
- segment_name: str
- segment_description: str
- rag_citations: list[RAGCitation]
"""

GraphNode = dict[str, Union[str, float, list[str], JSONObject]]
"""
Węzeł z Neo4j:
- type: str (Observation, Indicator, Trend, etc.)
- summary: str
- key_facts: list[str]
- confidence: float
- metadata: dict
"""

# ============================================================================
# Persona Types
# ============================================================================

PersonalityTraits = dict[str, float]
"""
Big Five traits (0.0-1.0):
- openness: float
- conscientiousness: float
- extraversion: float
- agreeableness: float
- neuroticism: float
"""

DemographicProfile = dict[str, Union[str, int, list[str]]]
"""
Profil demograficzny persony:
- age: int
- gender: str
- education_level: str
- income_bracket: str
- occupation: str
- location: str
- values: list[str]
- interests: list[str]
"""

# ============================================================================
# Dashboard/Analytics Types
# ============================================================================

UsageMetrics = dict[str, Union[int, float, str]]
"""
Metryki użycia:
- tokens_used: int
- cost: float
- operation: str
- model: str
"""

DemographicBreakdown = dict[str, dict[str, Union[int, float]]]
"""
Rozbicie demograficzne:
- by_age: dict[age_group, count]
- by_gender: dict[gender, count]
- by_education: dict[education, count]
- by_income: dict[income, count]
"""

# ============================================================================
# Workflow Types
# ============================================================================

WorkflowContext = dict[str, Union[str, int, bool, list[str], JSONObject]]
"""
Kontekst wykonania workflow:
- project_id: str
- user_id: str
- step: str
- variables: dict
- results: dict
"""

NodeResult = dict[str, Union[str, bool, int, JSONObject]]
"""
Wynik wykonania węzła workflow:
- status: str (success, failed, skipped)
- data: dict
- next_node: str (optional)
- error: str (optional)
"""

# ============================================================================
# API Types
# ============================================================================

APIError = dict[str, Union[str, int, list[str]]]
"""
Error response z API:
- detail: str
- status_code: int
- errors: list[str] (optional)
"""

PaginationParams = dict[str, int]
"""
Parametry paginacji:
- offset: int
- limit: int
"""

# ============================================================================
# Logging Types
# ============================================================================

LogContext = dict[str, Union[str, int, float, bool, None]]
"""
Kontekst logowania (structured logging):
- user_id: str
- project_id: str
- operation: str
- duration_ms: float
- status: str
"""
