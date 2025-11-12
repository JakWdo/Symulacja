"""Serwis RAG odpowiedzialny za hybrydowe wyszukiwanie.

Moduł udostępnia klasę :class:`PolishSocietyRAG` która realizuje hybrydowe
wyszukiwanie kontekstu (vector + keyword + RRF) wykorzystywane w generatorze person.

Dokumentacja i komentarze pozostają po polsku, aby ułatwić współpracę zespołu.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

import redis.asyncio as redis
from langchain_core.documents import Document

from config import rag, app
from app.services.rag.clients import get_vector_store
from app.services.rag.search.cache import (
    get_hybrid_search_cache_key,
    get_hybrid_cache,
    set_hybrid_cache,
)
from app.services.rag.search.keyword_search import (
    keyword_search,
    ensure_fulltext_index,
)
from app.services.rag.search.lucene_utils import sanitize_lucene_query
from app.services.rag.search.fusion_algorithms import rrf_fusion
from app.services.rag.search.reranker import init_reranker, rerank_with_cross_encoder
from app.services.rag.search.graph_enrichment import (
    format_graph_context,
    find_related_graph_nodes,
    enrich_chunk_with_graph,
)

logger = logging.getLogger(__name__)


class PolishSocietyRAG:
    """Hybrydowe wyszukiwanie kontekstu dla generatora person.

    Łączy wyszukiwanie semantyczne (embeddingi) oraz pełnotekstowe (fulltext index)
    korzystając z techniki Reciprocal Rank Fusion. Klasa jest niezależna od
    Graph RAG, ale współdzieli te same ustawienia i konwencję metadanych.
    """

    def __init__(self) -> None:
        """Przygotowuje wektorowe i keywordowe zaplecze wyszukiwawcze."""

        # Współdzielone połączenie z Neo4j Vector Store (retry logic w warstwie pomocniczej)
        self.vector_store = get_vector_store(logger)

        # Redis cache dla hybrid search queries (7-day TTL - same as GraphRAGService)
        self.redis_client: Optional[redis.Redis] = None
        try:
            self.redis_client = redis.from_url(
                app.redis.url,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("✅ PolishSocietyRAG: Redis cache enabled")
        except Exception as exc:
            logger.warning(
                "⚠️ PolishSocietyRAG: Redis unavailable - cache disabled. Error: %s",
                exc
            )

        if self.vector_store:
            logger.info("✅ PolishSocietyRAG: Neo4j Vector Store połączony")

            # Fulltext index będzie tworzony lazy - przy pierwszym użyciu keyword search
            # (nie możemy użyć asyncio.create_task() w __init__ bo może nie być event loop)
            self._fulltext_index_initialized = False

            # Leniwa inicjalizacja GraphRAGService dla dostępu do kontekstu grafowego
            self._graph_rag_service = None

            # Inicjalizuj cross-encoder dla reranking (opcjonalny)
            self.reranker = init_reranker()
        else:
            logger.error("❌ PolishSocietyRAG: Neo4j Vector Store failed - RAG wyłączony")
            self._fulltext_index_initialized = False
            self._graph_rag_service = None
            self.reranker = None

    @property
    def graph_rag_service(self):
        """Leniwa inicjalizacja GraphRAGService dla dostępu do strukturalnego kontekstu."""
        if self._graph_rag_service is None:
            from app.services.rag.graph import GraphRAGService

            self._graph_rag_service = GraphRAGService()
        return self._graph_rag_service

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 5
    ) -> list[Document]:
        """Wykonuje hybrydowe wyszukiwanie (vector + keyword + RRF fusion).

        NOWOŚĆ: Redis caching (7-day TTL) - cache hit rate ~70-90% expected.

        Ta metoda łączy wyszukiwanie semantyczne (embeddingi) i pełnotekstowe (keywords)
        używając Reciprocal Rank Fusion do połączenia wyników.

        Args:
            query: Zapytanie tekstowe do wyszukania
            top_k: Liczba wyników do zwrócenia (domyślnie 5)

        Returns:
            Lista Document obiektów posortowana po relevance score

        Raises:
            RuntimeError: Jeśli vector store nie jest dostępny
        """
        if not self.vector_store:
            raise RuntimeError("Vector store niedostępny - hybrid search niemożliwy")

        # === REDIS CACHE CHECK ===
        cache_key = get_hybrid_search_cache_key(query, top_k)
        cached_documents = await get_hybrid_cache(self.redis_client, cache_key)

        if cached_documents:
            logger.info(
                f"🚀 Hybrid search cache HIT - returning {len(cached_documents)} docs "
                f"(no vector/keyword search needed)"
            )
            return cached_documents

        logger.info("Hybrid search: query='%s...', top_k=%s", query[:50], top_k)

        try:
            import time
            search_start = time.perf_counter()

            # HYBRID SEARCH (Vector + Keyword)
            if rag.retrieval.use_hybrid_search:
                # Zwiększamy k aby mieć więcej candidates dla reranking
                candidates_k = rag.retrieval.rerank_candidates if rag.retrieval.use_reranking else top_k * 2

                # Lazy initialization fulltext index przy pierwszym użyciu
                if not self._fulltext_index_initialized:
                    await ensure_fulltext_index(self.vector_store)
                    self._fulltext_index_initialized = True

                # Vector search (timing)
                vector_start = time.perf_counter()
                vector_results = await self.vector_store.asimilarity_search_with_score(
                    query,
                    k=candidates_k,
                )
                vector_duration = time.perf_counter() - vector_start

                # Keyword search (timing)
                keyword_start = time.perf_counter()
                keyword_results = await keyword_search(
                    query=query,
                    k=candidates_k,
                    vector_store=self.vector_store,
                    sanitize_query_func=sanitize_lucene_query,
                )
                keyword_duration = time.perf_counter() - keyword_start

                # RRF fusion (timing)
                rrf_start = time.perf_counter()
                fused_results = rrf_fusion(
                    vector_results,
                    keyword_results,
                    k=rag.retrieval.rrf_k,
                )
                rrf_duration = time.perf_counter() - rrf_start

                # Optional reranking
                if rag.retrieval.use_reranking and self.reranker:
                    logger.info("Applying cross-encoder reranking")
                    final_results = await rerank_with_cross_encoder(
                        query=query,
                        candidates=fused_results[:rag.retrieval.rerank_candidates],
                        reranker=self.reranker,
                        top_k=top_k
                    )
                else:
                    final_results = fused_results[:top_k]

                # Performance metrics logging
                total_duration = time.perf_counter() - search_start
                logger.info(
                    "🔍 Hybrid search performance: vector=%.2fs | keyword=%.2fs | RRF=%.2fs | total=%.2fs",
                    vector_duration,
                    keyword_duration,
                    rrf_duration,
                    total_duration
                )
            else:
                # Vector-only search
                final_results = await self.vector_store.asimilarity_search_with_score(
                    query,
                    k=top_k,
                )

            # Return only Documents (strip scores)
            documents = [doc for doc, score in final_results]
            logger.info("Hybrid search returned %s documents", len(documents))

            # === CACHE RESULT ===
            # Cache the result for future requests (7-day TTL)
            await set_hybrid_cache(self.redis_client, cache_key, documents)

            return documents

        except Exception as exc:
            logger.error("Hybrid search failed: %s", exc, exc_info=True)
            raise RuntimeError(f"Hybrid search failed: {exc}")

    async def get_demographic_insights(
        self,
        age_group: str,
        education: str,
        location: str,
        gender: str,
    ) -> dict[str, Any]:
        """Buduje kontekst raportowy dla wskazanego profilu demograficznego.

        Łączy trzy źródła kontekstu:
        1. **Graph RAG** - Strukturalna wiedza z grafu (Indicators, Observations, Trends)
        2. **Vector Search** - Semantyczne wyszukiwanie w embeddingach
        3. **Keyword Search** - Leksykalne wyszukiwanie fulltext (opcjonalnie)

        Returns:
            Dict z kluczami:
            - context: Pełny kontekst (graph + chunks tekstowe)
            - graph_context: Sformatowany kontekst z grafu (string)
            - graph_nodes: Surowe węzły grafu (list)
            - citations: Citations z hybrid search
            - query: Query użyte do wyszukiwania
            - num_results: Liczba wyników z hybrid search
            - search_type: "hybrid+graph" | "vector_only+graph" | "hybrid" | "vector_only"
        """

        if not self.vector_store:
            logger.warning("Vector store niedostępny – zwracam pusty kontekst.")
            return {"context": "", "citations": [], "query": "", "num_results": 0}

        query = (
            f"Profil demograficzny: {gender}, wiek {age_group}, wykształcenie {education}, "
            f"lokalizacja {location} w Polsce. Jakie są typowe cechy, wartości, zainteresowania, "
            f"style życia oraz aspiracje dla tej grupy?"
        )

        logger.info(
            "RAG hybrid search + Graph RAG dla profilu: wiek=%s, edukacja=%s, lokalizacja=%s, płeć=%s",
            age_group,
            education,
            location,
            gender,
        )

        try:
            # 1. GRAPH RAG - Pobierz strukturalny kontekst z grafu wiedzy
            graph_nodes = []
            graph_context_formatted = ""

            try:
                import inspect

                # Timeout dla Graph RAG query (domyślnie 30s)
                async def get_graph_context_with_timeout():
                    # WAŻNE: get_demographic_graph_context jest async – MUSI być awaitowane
                    result = await self.graph_rag_service.get_demographic_graph_context(
                        age_group=age_group,
                        location=location,
                        education=education,
                        gender=gender,
                    )

                    # DEFENSIVE CHECK: Ensure result is not a coroutine
                    if inspect.iscoroutine(result):
                        logger.error(
                            "❌ BUG: get_demographic_graph_context returned a coroutine instead of list! "
                            "This should never happen - returning empty list"
                        )
                        # Clean up the unawaited coroutine to prevent warning
                        result.close()
                        return []

                    return result

                graph_nodes = await asyncio.wait_for(
                    get_graph_context_with_timeout(),
                    timeout=30,  # Default 30s timeout
                )

                # DEFENSIVE CHECK: Validate graph_nodes type before using
                if not isinstance(graph_nodes, list):
                    logger.error(
                        "❌ BUG: graph_nodes is not a list (type: %s)! "
                        "Resetting to empty list to prevent crash",
                        type(graph_nodes).__name__
                    )
                    # If it's a coroutine, close it to prevent warning
                    if inspect.iscoroutine(graph_nodes):
                        graph_nodes.close()
                    graph_nodes = []

                if graph_nodes:
                    graph_context_formatted = format_graph_context(graph_nodes)
                    logger.info("Pobrano %s węzłów grafu z kontekstem demograficznym", len(graph_nodes))
                else:
                    logger.info("Brak wyników z graph context dla podanego profilu")
            except asyncio.TimeoutError:
                logger.warning(
                    "Graph RAG timeout po 30s - kontynuacja bez graph context"
                )
                graph_nodes = []  # Explicitly reset
            except Exception as graph_exc:
                logger.error(
                    "Nie udało się pobrać graph context: %s - kontynuacja bez graph context",
                    graph_exc,
                    exc_info=True  # Full traceback for debugging
                )
                graph_nodes = []  # Explicitly reset

            # 2. HYBRID SEARCH (Vector + Keyword) - Pobierz chunki tekstowe
            # Lazy initialization fulltext index przy pierwszym użyciu
            if rag.retrieval.use_hybrid_search and not self._fulltext_index_initialized:
                await ensure_fulltext_index(self.vector_store)
                self._fulltext_index_initialized = True

            if rag.retrieval.use_hybrid_search:
                # Zwiększamy k aby mieć więcej candidates dla reranking
                candidates_k = rag.retrieval.rerank_candidates if rag.retrieval.use_reranking else rag.retrieval.top_k * 2

                vector_results = await self.vector_store.asimilarity_search_with_score(
                    query,
                    k=candidates_k,
                )
                keyword_results = await keyword_search(
                    query=query,
                    k=candidates_k,
                    vector_store=self.vector_store,
                    sanitize_query_func=sanitize_lucene_query,
                )
                fused_results = rrf_fusion(
                    vector_results,
                    keyword_results,
                    k=rag.retrieval.rrf_k,
                )

                # 2b. RERANKING (opcjonalne) - Precyzyjny re-scoring z cross-encoder
                if rag.retrieval.use_reranking and self.reranker:
                    logger.info("Applying cross-encoder reranking on top %s candidates", len(fused_results))
                    final_results = await rerank_with_cross_encoder(
                        query=query,
                        candidates=fused_results[:rag.retrieval.rerank_candidates],
                        reranker=self.reranker,
                        top_k=rag.retrieval.top_k
                    )
                    search_type = "hybrid+rerank+graph" if graph_nodes else "hybrid+rerank"
                else:
                    final_results = fused_results[:rag.retrieval.top_k]
                    search_type = "hybrid+graph" if graph_nodes else "hybrid"
            else:
                final_results = await self.vector_store.asimilarity_search_with_score(
                    query,
                    k=rag.retrieval.top_k,
                )
                search_type = "vector_only+graph" if graph_nodes else "vector_only"

            # 3. UNIFIED CONTEXT - Wzbogać chunki o powiązane graph nodes
            context_chunks: list[str] = []
            citations: list[dict[str, Any]] = []
            enriched_chunks_count = 0

            # Dodaj graph context na początku (jeśli istnieje)
            if graph_context_formatted:
                context_chunks.append("=== STRUKTURALNA WIEDZA Z GRAFU WIEDZY ===\n")
                context_chunks.append(graph_context_formatted)
                context_chunks.append("\n=== KONTEKST Z DOKUMENTÓW (WZBOGACONY) ===\n")

            # Dodaj chunki tekstowe WZBOGACONE o powiązane graph nodes
            for doc, score in final_results:
                # Znajdź graph nodes powiązane z tym chunkiem
                related_nodes = find_related_graph_nodes(doc, graph_nodes)

                # Wzbogać chunk jeśli są related nodes
                if related_nodes:
                    enriched_text = enrich_chunk_with_graph(
                        chunk_text=doc.page_content,
                        related_nodes=related_nodes
                    )
                    enriched_chunks_count += 1
                else:
                    enriched_text = doc.page_content

                # Truncate jeśli za długi
                if len(enriched_text) > 1000:
                    enriched_text = enriched_text[:1000] + "\n[...fragment obcięty...]"

                context_chunks.append(enriched_text)
                # Format zgodny z RAGCitation schema (app/schemas/rag.py)
                citations.append(
                    {
                        "document_title": doc.metadata.get("title", "Unknown Document"),
                        "chunk_text": doc.page_content[:500],  # Original dla citation
                        "relevance_score": float(score),
                    }
                )

            if enriched_chunks_count > 0:
                logger.info(
                    "Unified context: %s/%s chunks enriched with graph nodes",
                    enriched_chunks_count,
                    len(final_results)
                )

            context = "\n\n---\n\n".join(context_chunks)
            if len(context) > rag.retrieval.max_context_chars:
                context = context[: rag.retrieval.max_context_chars] + "\n\n[... kontekst obcięty]"

            return {
                "context": context,
                "graph_context": graph_context_formatted,
                "graph_nodes": graph_nodes,
                "graph_nodes_count": len(graph_nodes),
                "citations": citations,
                "query": query,
                "num_results": len(final_results),
                "search_type": search_type,
                "enriched_chunks_count": enriched_chunks_count,
            }
        except Exception as exc:  # pragma: no cover - zwracamy pusty kontekst
            logger.error("Hybrydowe wyszukiwanie nie powiodło się: %s", exc, exc_info=True)
            return {"context": "", "citations": [], "query": query, "num_results": 0}
