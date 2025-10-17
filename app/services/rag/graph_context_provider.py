"""
GraphContextProvider - Wrapper nad GraphRAGService dla Persona Narratives

Upraszcza dostęp do kontekstu grafowego dla potrzeb generowania narracji.
Wrapper izoluje logikę narratives od szczegółów GraphRAG API.

Performance:
- Cache GraphRAG queries (5min TTL)
- Limit results dla performance (default 10 nodes, 5 insights)
- Graceful degradation (return [] jeśli GraphRAG nie działa)

Examples:
    >>> provider = GraphContextProvider()
    >>> nodes = await provider.get_segment_nodes(persona, limit=10)
    >>> insights = await provider.get_top_insights(persona, limit=5)
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from app.models import Persona
from app.services.rag.rag_graph_service import GraphRAGService
from app.core.redis import redis_get_json, redis_set_json

logger = logging.getLogger(__name__)


def _age_to_age_group(age: Optional[int]) -> str:
    """Mapuje wiek na bucket używany w Graph/Hybrid RAG."""
    if age is None:
        return "25-34"
    if age < 18:
        return "0-17"
    if age <= 24:
        return "18-24"
    if age <= 34:
        return "25-34"
    if age <= 44:
        return "35-44"
    if age <= 54:
        return "45-54"
    if age <= 64:
        return "55-64"
    return "65+"


def _normalize_gender(gender: Optional[str]) -> str:
    """Normalizuje płeć do formatu akceptowanego przez Graph/Hybrid RAG."""
    if not gender:
        return "osoby"

    value = gender.strip().lower()
    mapping = {
        "female": "kobieta",
        "kobieta": "kobieta",
        "woman": "kobieta",
        "male": "mężczyzna",
        "mężczyzna": "mężczyzna",
        "man": "mężczyzna",
        "non-binary": "osoba niebinarna",
        "nonbinary": "osoba niebinarna",
        "osoba niebinarna": "osoba niebinarna",
        "other": "osoby",
    }
    return mapping.get(value, value or "osoby")


def _normalize_text(value: Optional[str], fallback: str) -> str:
    """Zwraca przycięty tekst lub domyślną wartość, jeśli brak danych."""
    if not value:
        return fallback
    return str(value).strip() or fallback


class GraphContextProvider:
    """
    Wrapper nad GraphRAGService upraszczający dostęp do kontekstu grafowego.

    Responsibilities:
    - Fetch segment nodes (demographic context z Neo4j)
    - Fetch top insights (sorted by confidence)
    - Cache results w Redis (TTL 5min)
    - Graceful degradation (return [] on error)

    Performance:
    - Cache hit: <10ms (Redis)
    - Cache miss: <500ms (Neo4j query)
    """

    def __init__(self):
        self.graph_rag = GraphRAGService()

    async def get_segment_nodes(
        self,
        persona: Persona,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Pobiera węzły demograficzne z GraphRAG dla segmentu persony.

        Args:
            persona: Persona object
            limit: Max liczba węzłów (default 10)

        Returns:
            Lista węzłów grafu z metadata (type, summary, confidence, etc.)
        """
        cache_key = f"graph_nodes:{persona.id}:{limit}"

        cached = await redis_get_json(cache_key)
        if cached is not None:
            logger.debug(
                "Graph nodes cache hit for persona %s", persona.id,
                extra={"persona_id": str(persona.id), "nodes_count": len(cached)}
            )
            return cached

        try:
            age_group = _age_to_age_group(getattr(persona, "age", None))
            gender = _normalize_gender(getattr(persona, "gender", None))
            location = _normalize_text(getattr(persona, "location", None), "Polska")
            education = _normalize_text(getattr(persona, "education_level", None), "wyższe")

            nodes = await asyncio.to_thread(
                self.graph_rag.get_demographic_graph_context,
                age_group,
                location,
                education,
                gender,
            )

            valid_nodes = [
                node for node in nodes
                if node.get("summary") or node.get("streszczenie")
            ]

            await redis_set_json(cache_key, valid_nodes, ttl_seconds=300)

            logger.info(
                "Fetched %s graph nodes for persona %s",
                len(valid_nodes),
                persona.id,
                extra={
                    "persona_id": str(persona.id),
                    "nodes_count": len(valid_nodes),
                    "source": "graphrag",
                    "age_group": age_group,
                    "gender": gender,
                    "location": location,
                    "education": education,
                }
            )

            return valid_nodes

        except Exception as e:
            logger.warning(
                "Failed to fetch graph nodes for persona %s: %s",
                persona.id,
                e,
                exc_info=e,
                extra={"persona_id": str(persona.id)}
            )
            return []

    async def get_top_insights(
        self,
        persona: Persona,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Pobiera top insights z GraphRAG sorted by confidence."""
        nodes = await self.get_segment_nodes(persona, limit=limit * 2)

        if not nodes:
            return []

        confidence_priority = {
            "high": 3,
            "wysoka": 3,
            "medium": 2,
            "średnia": 2,
            "srednia": 2,
            "low": 1,
            "niska": 1,
        }

        sorted_nodes = sorted(
            nodes,
            key=lambda x: confidence_priority.get(
                str(x.get("confidence", "")).lower(),
                0
            ),
            reverse=True
        )

        top_insights = sorted_nodes[:limit]

        logger.debug(
            "Extracted %s top insights for persona %s",
            len(top_insights),
            persona.id,
            extra={
                "persona_id": str(persona.id),
                "total_nodes": len(nodes),
                "top_count": len(top_insights)
            }
        )

        return top_insights
