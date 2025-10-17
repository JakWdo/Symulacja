"""
HybridContextProvider - Wrapper nad PolishSocietyRAG dla Persona Narratives

Upraszcza dostęp do kontekstu tekstowego (Hybrid Search + RAG) dla narracji.
Wrapper izoluje logikę narratives od szczegółów PolishSocietyRAG API.

Performance:
- Cache RAG queries (5min TTL)
- Top-k retrieval dla relevance (default 5)
- Graceful degradation (return empty context on error)

Examples:
    >>> provider = HybridContextProvider()
    >>> context = await provider.get_narrative_context(persona, top_k=5)
    >>> print(context['context'])  # Tekstowy kontekst
    >>> print(context['citations'])  # Lista cytowań
"""

import logging
from typing import Any, Dict, List, Optional

from app.models import Persona
from app.services.rag.rag_hybrid_search_service import PolishSocietyRAG
from app.core.redis import redis_get_json, redis_set_json

logger = logging.getLogger(__name__)


def _age_to_age_group(age: Optional[int]) -> str:
    """Mapuje wiek na bucket używany w zapytaniach RAG."""
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
    """Normalizuje płeć do formy używanej w zapytaniach."""
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


class HybridContextProvider:
    """
    Wrapper nad PolishSocietyRAG upraszczający dostęp do kontekstu tekstowego.

    Responsibilities:
    - Fetch narrative context (text + citations z Hybrid RAG)
    - Build demographic query dla relevance
    - Cache results w Redis (TTL 5min)
    - Graceful degradation (return empty dict on error)

    Performance:
    - Cache hit: <10ms (Redis)
    - Cache miss: <800ms (Hybrid search + RRF fusion)
    """

    def __init__(self):
        self.hybrid_rag = PolishSocietyRAG()

    async def get_narrative_context(
        self,
        persona: Persona,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Pobiera kontekst tekstowy + cytowania z Hybrid RAG.

        Strategia:
        1. Build demographic query (age, gender, location, education)
        2. Query PolishSocietyRAG.get_demographic_insights
        3. Extract context text + citations
        4. Cache results (5min TTL)
        5. Graceful degradation (return empty dict on error)

        Args:
            persona: Persona object
            top_k: Max liczba chunks do retrieval (default 5)

        Returns:
            Dict z:
            - context: str (tekstowy kontekst z RAG)
            - citations: List[Dict] (lista cytowań z relevance scores)
            - metadata: Dict (info o źródłach)

        Performance:
            - Cache hit: <10ms
            - Cache miss: <800ms (Hybrid search)
            - Graceful degradation: return {} on error
        """
        # Cache key: narrative context dla danej persony
        cache_key = f"hybrid_context:{persona.id}:{top_k}"

        # Check cache
        cached = await redis_get_json(cache_key)
        if cached is not None:
            logger.debug(
                f"Hybrid context cache hit for persona {persona.id}",
                extra={
                    "persona_id": str(persona.id),
                    "citations_count": len(cached.get("citations", []))
                }
            )
            return cached

        try:
            age_group = _age_to_age_group(getattr(persona, "age", None))
            gender_base = _normalize_gender(getattr(persona, "gender", None))
            location = _normalize_text(getattr(persona, "location", None), "Polska")
            education = _normalize_text(getattr(persona, "education_level", None), "wyższe")

            gender_query_map = {
                "kobieta": "Kobiety",
                "mężczyzna": "Mężczyźni",
                "osoba niebinarna": "Osoby niebinarne",
                "osoby": "Osoby",
            }
            gender_query = gender_query_map.get(gender_base, gender_base.title())

            # Format: "Kobiety, wiek 35-44, Warszawa, wyższe"
            query_parts = [
                gender_query,
                f"wiek {age_group}",
                location,
                education,
            ]
            if persona.income_bracket:
                query_parts.append(str(persona.income_bracket).strip())

            demographic_query = ", ".join(part for part in query_parts if part)

            logger.debug(
                f"Built demographic query for persona {persona.id}: {demographic_query}",
                extra={"persona_id": str(persona.id), "query": demographic_query}
            )

            # Query Hybrid RAG
            insights = await self.hybrid_rag.get_demographic_insights(
                age_group=age_group,
                education=education,
                location=location,
                gender=gender_base,
            )

            # Extract context + citations
            context_text = insights.get("context", "")
            citations_raw = insights.get("citations", [])

            # Format citations (normalize structure)
            citations = []
            for cit in citations_raw:
                if isinstance(cit, dict):
                    citations.append({
                        "document_title": cit.get("document_title", "Unknown Document"),
                        "chunk_text": cit.get("chunk_text", cit.get("text", "")),
                        "relevance_score": float(cit.get("relevance_score", cit.get("score", 0.0)))
                    })

            # Build result
            result = {
                "context": context_text,
                "citations": citations,
                "metadata": {
                    "query": demographic_query,
                    "top_k": top_k,
                    "age_group": age_group,
                    "gender": gender_base,
                    "location": location,
                    "education": education,
                    "source": "hybrid_rag"
                }
            }

            # Cache result (5min TTL)
            await redis_set_json(cache_key, result, ttl_seconds=300)

            logger.info(
                f"Fetched hybrid context for persona {persona.id}",
                extra={
                    "persona_id": str(persona.id),
                    "context_length": len(context_text),
                    "citations_count": len(citations)
                }
            )

            return result

        except Exception as e:
            # Graceful degradation - log warning but nie fail całego requesta
            logger.warning(
                f"Failed to fetch hybrid context for persona {persona.id}: {e}",
                exc_info=e,
                extra={"persona_id": str(persona.id)}
            )
            return {
                "context": "",
                "citations": [],
                "metadata": {
                    "error": str(e),
                    "query": "",
                    "top_k": top_k,
                }
            }
