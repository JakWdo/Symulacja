"""Pydantic models i helper functions dla orchestration module.

Ten moduł zawiera data classes używane przez PersonaOrchestrationService:
- GraphInsight: Single insight z grafu wiedzy
- DemographicGroup: Grupa demograficzna z briefem i insights
- PersonaAllocationPlan: Kompletny plan alokacji person
- map_graph_node_to_insight: Helper dla konwersji PL → EN property names
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


def map_graph_node_to_insight(node: dict[str, Any]) -> "GraphInsight" | None:
    """Konwertuje graph node z polskimi property names na GraphInsight z angielskimi.

    Mapowanie:
    - streszczenie → summary
    - skala → magnitude
    - pewnosc → confidence ("wysoka"→"high", "srednia"→"medium", "niska"→"low")
    - okres_czasu → time_period
    - kluczowe_fakty → why_matters (z dodatkowym kontekstem)

    Args:
        node: Dict z grafu Neo4j (polskie property names)

    Returns:
        GraphInsight object lub None jeśli dane niepełne
    """
    if not node:
        return None

    # Graf używa polskich property names
    node_type = node.get('type', 'Unknown')
    summary = node.get('streszczenie')

    if not summary:
        logger.warning(f"Graph node bez streszczenia: {node}")
        return None

    # Mapowanie pewności PL→EN
    pewnosc_pl = node.get('pewnosc', '').lower()
    confidence_map = {'wysoka': 'high', 'srednia': 'medium', 'niska': 'low'}
    confidence = confidence_map.get(pewnosc_pl, 'medium')

    # Dane węzła (polskie property names)
    magnitude = node.get('skala')
    time_period = node.get('okres_czasu')
    source = node.get('source', node.get('document_title'))

    # why_matters - użyj kluczowych faktów lub summary jako fallback
    kluczowe_fakty = node.get('kluczowe_fakty', '')
    why_matters = f"Ten wskaźnik pokazuje: {kluczowe_fakty}" if kluczowe_fakty else summary

    try:
        return GraphInsight(
            type=node_type,
            summary=summary,
            magnitude=magnitude,
            confidence=confidence,
            time_period=time_period,
            source=source,
            why_matters=why_matters
        )
    except Exception as e:
        logger.error(f"Nie można utworzyć GraphInsight z node: {node}, error: {e}")
        return None


class GraphInsight(BaseModel):
    """Pojedynczy insight z grafu wiedzy (Wskaznik, Obserwacja, Trend).

    UWAGA: Ten schema używa ANGIELSKICH property names dla API consistency.
    Dane w grafie Neo4j używają POLSKICH nazw (streszczenie, skala, pewnosc, etc.).

    Konwersja wykonywana przez funkcję map_graph_node_to_insight():
    - streszczenie → summary
    - skala → magnitude
    - pewnosc → confidence ("wysoka"→"high", "srednia"→"medium", "niska"→"low")
    - okres_czasu → time_period
    - kluczowe_fakty → why_matters (z dodatkowym edukacyjnym kontekstem)
    """

    type: str = Field(description="Typ węzła (Wskaznik, Obserwacja, Trend, etc.)")
    summary: str = Field(description="Jednozdaniowe podsumowanie")
    magnitude: str | None = Field(default=None, description="Wartość liczbowa jeśli istnieje (np. '78.4%')")
    confidence: str = Field(default="medium", description="Poziom pewności: high, medium, low")
    time_period: str | None = Field(default=None, description="Okres czasu (np. '2022')")
    source: str | None = Field(default=None, description="Źródło danych (np. 'GUS', 'CBOS')")
    why_matters: str = Field(description="Edukacyjne wyjaśnienie dlaczego to ważne dla person")


class DemographicGroup(BaseModel):
    """Grupa demograficzna z briefem i insightami."""

    count: int = Field(description="Liczba person do wygenerowania w tej grupie")
    demographics: dict[str, Any] = Field(description="Cechy demograficzne (age, gender, education, etc.)")
    brief: str = Field(description="Długi (900-1200 znaków) edukacyjny brief dla generatorów")
    graph_insights: list[GraphInsight] = Field(default_factory=list, description="Insighty z Graph RAG")
    allocation_reasoning: str = Field(description="Dlaczego tyle person w tej grupie")
    segment_characteristics: list[str] = Field(default_factory=list, description="4-6 kluczowych cech tego segmentu (np. 'Profesjonaliści z wielkich miast')")


class PersonaAllocationPlan(BaseModel):
    """Plan alokacji person z szczegółowymi briefami dla każdej grupy."""

    total_personas: int = Field(description="Całkowita liczba person do wygenerowania")
    groups: list[DemographicGroup] = Field(description="Grupy demograficzne z briefami")
    overall_context: str = Field(description="Ogólny kontekst społeczny Polski z Graph RAG")
