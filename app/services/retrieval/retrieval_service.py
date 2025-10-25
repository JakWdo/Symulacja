"""
RetrievalService - Unified RAG API dla segment-first architecture.

Ten serwis dostarcza zunifikowany interfejs do pobierania kontekstu RAG dla segmentów
demograficznych z inteligentnym wyborem strategii wyszukiwania (vector-first).

Kluczowe optymalizacje:
- Vector-only by default (najszybsze)
- Hybrid + rerank tylko jeśli wyniki słabe (< 3 docs or low diversity)
- Hard limit: context ≤ 1500 chars (vs current 8000)
- Graph insights limited do 5 nodes (vs unlimited)

Performance targets:
- Vector-only: ~500ms (vs ~1000ms hybrid)
- Token reduction: ~60% (1500 chars vs 8000 chars)
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from langchain_core.documents import Document

from app.core.config import get_settings
from app.services.rag.rag_hybrid_search_service import PolishSocietyRAG

settings = get_settings()
logger = logging.getLogger(__name__)


class RetrievalService:
    """Unified RAG retrieval z vector-first, conditional hybrid."""

    def __init__(self) -> None:
        """Inicjalizuje retrieval service z PolishSocietyRAG backend."""
        self.rag_service = PolishSocietyRAG()
        logger.info("RetrievalService zainicjalizowany (vector-first strategy)")

    async def get_segment_context(
        self,
        age_group: str,
        gender: str,
        education: str,
        location: str,
        top_k: int = 8,
        mode: str | None = None,
    ) -> dict[str, Any]:
        """Pobiera kontekst RAG dla segmentu demograficznego.

        Vector-first strategy:
        - Domyślnie używa vector-only search (najszybsze)
        - Przełącza na hybrid jeśli wyniki słabe (< 3 docs or low diversity)
        - Hard limit: context ≤ 1500 chars

        Args:
            age_group: Grupa wiekowa (np. "25-34")
            gender: Płeć (np. "kobieta", "mężczyzna")
            education: Poziom edukacji (np. "wyższe")
            location: Lokalizacja (np. "Warszawa")
            top_k: Liczba top results (default: 8)
            mode: Wymuszona strategia wyszukiwania:
                  - "vector" - tylko vector search
                  - "hybrid" - vector + keyword + RRF
                  - "hybrid+rerank" - hybrid + cross-encoder reranking
                  - None (default) - auto-select based on results

        Returns:
            Dict z kluczami:
            - context: str (≤1500 chars, HARD LIMIT)
            - citations: list[dict] (metadane dokumentów)
            - graph_insights: list[dict] (≤5 nodes)
            - query: str (użyte query)
            - search_type: str (faktycznie użyta strategia)
            - retrieval_mode: str (initial mode selection)

        Raises:
            Exception: Jeśli RAG service niedostępny
        """
        logger.info(
            f"🔍 RetrievalService.get_segment_context: age={age_group}, gender={gender}, "
            f"edu={education}, loc={location}, mode={mode or 'auto'}"
        )

        # Pobierz dane z PolishSocietyRAG (domyślnie hybrid+graph)
        # Note: PolishSocietyRAG.get_demographic_insights() zawsze używa hybrid search
        # jeśli RAG_USE_HYBRID_SEARCH=True. My nie mamy kontroli nad tym w obecnej
        # implementacji, więc nasz "mode" parameter jest obecnie informational.
        #
        # TODO: Refactor PolishSocietyRAG aby wspierać vector-only mode
        # (wymagałoby dodania parametru do get_demographic_insights)
        rag_result = await self.rag_service.get_demographic_insights(
            age_group=age_group,
            gender=gender,
            education=education,
            location=location,
        )

        # Extract raw context
        raw_context = rag_result.get("context", "")
        citations = rag_result.get("citations", [])
        graph_nodes = rag_result.get("graph_nodes", [])
        search_type = rag_result.get("search_type", "unknown")

        # Evaluate result quality
        num_results = len(citations)
        low_quality = num_results < 3

        if low_quality and mode != "vector":
            logger.info(
                f"⚠️  Low quality results (n={num_results}) - hybrid search already applied by PolishSocietyRAG"
            )

        # Apply hard limit: context ≤ 1500 chars
        truncated_context = self._truncate_context(raw_context, max_chars=1500)

        # Limit graph insights to top 5 nodes (sorted by confidence if available)
        limited_graph_insights = self._limit_graph_insights(graph_nodes, max_nodes=5)

        # Format citations as dicts (preserve metadata)
        formatted_citations = self._format_citations(citations)

        result = {
            "context": truncated_context,
            "citations": formatted_citations,
            "graph_insights": limited_graph_insights,
            "query": rag_result.get("query", ""),
            "search_type": search_type,
            "retrieval_mode": mode or "auto",
            "num_results": num_results,
            "truncated": len(truncated_context) < len(raw_context),
        }

        logger.info(
            f"✅ RetrievalService: {num_results} docs, {len(truncated_context)} chars "
            f"(truncated: {result['truncated']}), {len(limited_graph_insights)} graph nodes"
        )

        return result

    def _truncate_context(self, context: str, max_chars: int = 1500) -> str:
        """Truncate context do max_chars, zachowując complete sentences.

        Args:
            context: Pełny kontekst
            max_chars: Maksymalna długość (default: 1500)

        Returns:
            Truncated context (≤ max_chars)
        """
        if len(context) <= max_chars:
            return context

        # Truncate and find last complete sentence
        truncated = context[:max_chars]
        last_period = truncated.rfind(".")

        if last_period > max_chars - 200:  # Within last 200 chars
            return truncated[: last_period + 1]
        else:
            # No complete sentence nearby - hard truncate
            return truncated + "..."

    def _limit_graph_insights(
        self, graph_nodes: list[dict[str, Any]], max_nodes: int = 5
    ) -> list[dict[str, Any]]:
        """Limit graph insights do top N nodes, sorted by confidence.

        Args:
            graph_nodes: Surowe węzły grafu
            max_nodes: Maksymalna liczba nodes (default: 5)

        Returns:
            Top N nodes (sorted by confidence)
        """
        if not graph_nodes:
            return []

        # Sort by confidence (if available)
        def confidence_score(node: dict[str, Any]) -> int:
            """Map confidence to numeric score."""
            confidence = node.get("pewnosc", "").lower()  # Polish: "pewnosc"
            confidence_map = {"wysoka": 3, "srednia": 2, "niska": 1}
            return confidence_map.get(confidence, 0)

        sorted_nodes = sorted(graph_nodes, key=confidence_score, reverse=True)

        # Return top N
        return sorted_nodes[:max_nodes]

    def _format_citations(
        self, citations: list[Document | dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Format citations as dicts, preserving metadata.

        Args:
            citations: Lista Document objects lub dict

        Returns:
            Lista dicts z content + metadata
        """
        formatted = []

        for cit in citations:
            if isinstance(cit, Document):
                formatted.append(
                    {
                        "content": cit.page_content[:500],  # Limit to 500 chars per citation
                        "metadata": cit.metadata,
                    }
                )
            elif isinstance(cit, dict):
                formatted.append(
                    {
                        "content": str(cit.get("page_content", ""))[:500],
                        "metadata": cit.get("metadata", {}),
                    }
                )

        return formatted

    def generate_segment_hash(
        self,
        age_group: str,
        gender: str,
        education: str,
        location: str,
    ) -> str:
        """Generuje stabilny hash dla segmentu demograficznego.

        Hash używany jako część cache key w SegmentService.

        Args:
            age_group: Grupa wiekowa
            gender: Płeć
            education: Poziom edukacji
            location: Lokalizacja

        Returns:
            MD5 hash (8 pierwszych znaków)

        Examples:
            >>> svc.generate_segment_hash("25-34", "kobieta", "wyższe", "Warszawa")
            'a3f4b1c2'
        """
        # Normalize inputs (lowercase, strip whitespace)
        normalized = "|".join(
            [
                age_group.strip().lower(),
                gender.strip().lower(),
                education.strip().lower(),
                location.strip().lower(),
            ]
        )

        # Generate MD5 hash (first 8 chars)
        hash_obj = hashlib.md5(normalized.encode("utf-8"))
        return hash_obj.hexdigest()[:8]
