"""Serwisy RAG odpowiedzialne za budowę grafu wiedzy i hybrydowe wyszukiwanie.

Moduł udostępnia dwie komplementarne klasy:

* :class:`RAGDocumentService` – odpowiada za pełny pipeline przetwarzania
  dokumentów (ingest), utrzymanie indeksu wektorowego oraz grafu wiedzy w Neo4j
  i obsługę zapytań Graph RAG.
* :class:`PolishSocietyRAG` – realizuje hybrydowe wyszukiwanie kontekstu
  (vector + keyword + RRF) wykorzystywane w generatorze person.

Dokumentacja i komentarze pozostają po polsku, aby ułatwić współpracę zespołu.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from typing import Any

import redis.asyncio as redis
from langchain_core.documents import Document

from config import rag, app
from app.services.rag.rag_clients import get_vector_store

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
        self.redis_client = None
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

        # Cache TTL (7 days - same as GraphRAGService)
        self.CACHE_TTL_SECONDS = 7 * 24 * 60 * 60  # 604800 seconds

        if self.vector_store:
            logger.info("✅ PolishSocietyRAG: Neo4j Vector Store połączony")

            # Fulltext index będzie tworzony lazy - przy pierwszym użyciu keyword search
            # (nie możemy użyć asyncio.create_task() w __init__ bo może nie być event loop)
            self._fulltext_index_initialized = False

            # Leniwa inicjalizacja GraphRAGService dla dostępu do kontekstu grafowego
            self._graph_rag_service = None

            # Inicjalizuj cross-encoder dla reranking (opcjonalny)
            self.reranker = None
            if rag.retrieval.use_reranking:
                try:
                    from sentence_transformers import CrossEncoder
                    self.reranker = CrossEncoder(
                        rag.retrieval.reranker_model,
                        max_length=512
                    )
                    logger.info(
                        "Cross-encoder reranker zainicjalizowany: %s",
                        rag.retrieval.reranker_model
                    )
                except ImportError:
                    logger.warning(
                        "sentence-transformers nie jest zainstalowany - reranking wyłączony. "
                        "Zainstaluj: pip install sentence-transformers"
                    )
                except Exception as rerank_exc:
                    logger.warning(
                        "Nie udało się załadować reranker: %s - kontynuacja bez rerankingu",
                        rerank_exc
                    )
        else:
            logger.error("❌ PolishSocietyRAG: Neo4j Vector Store failed - RAG wyłączony")
            self._fulltext_index_initialized = False
            self._graph_rag_service = None
            self.reranker = None

    @property
    def graph_rag_service(self):
        """Leniwa inicjalizacja GraphRAGService dla dostępu do strukturalnego kontekstu."""
        if self._graph_rag_service is None:
            from app.services.rag.rag_graph_service import GraphRAGService

            self._graph_rag_service = GraphRAGService()
        return self._graph_rag_service

    def _get_hybrid_search_cache_key(self, query: str, top_k: int) -> str:
        """Generate cache key for hybrid search.

        Args:
            query: Search query text
            top_k: Number of results

        Returns:
            Cache key string (format: "hybrid_search:query_hash:topk")
        """
        # Hash query for shorter cache key (MD5 sufficient for caching)
        query_normalized = query.lower().strip()
        query_hash = hashlib.md5(query_normalized.encode()).hexdigest()[:12]

        return f"hybrid_search:{query_hash}:{top_k}"

    async def _get_hybrid_cache(self, cache_key: str) -> list[Document] | None:
        """Get cached hybrid search results from Redis.

        Args:
            cache_key: Redis key

        Returns:
            Cached documents (list of Document) or None if cache miss
        """
        if not self.redis_client:
            return None

        try:
            cached = await self.redis_client.get(cache_key)
            if cached:
                logger.info(f"✅ Hybrid search cache HIT for {cache_key}")
                # Deserialize JSON back to Document objects
                docs_data = json.loads(cached)
                documents = [
                    Document(
                        page_content=doc_data["page_content"],
                        metadata=doc_data.get("metadata", {})
                    )
                    for doc_data in docs_data
                ]
                return documents
            else:
                logger.info(f"❌ Hybrid search cache MISS for {cache_key}")
                return None
        except Exception as exc:
            logger.warning(f"⚠️ Redis get failed: {exc}")
            return None

    async def _set_hybrid_cache(self, cache_key: str, documents: list[Document]) -> None:
        """Store hybrid search results in Redis cache.

        Args:
            cache_key: Redis key
            documents: List of Document objects
        """
        if not self.redis_client:
            return

        try:
            # Serialize Document objects to JSON
            docs_data = [
                {
                    "page_content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in documents
            ]

            await self.redis_client.setex(
                cache_key,
                self.CACHE_TTL_SECONDS,
                json.dumps(docs_data, ensure_ascii=False)
            )
            logger.info(
                f"💾 Cached hybrid search: {cache_key} "
                f"({len(documents)} docs, TTL 7 days)"
            )
        except Exception as exc:
            logger.warning(f"⚠️ Redis set failed: {exc}")

    def _sanitize_lucene_query(self, query: str) -> str:
        """Sanityzuje query dla Lucene fulltext search - escape znaków specjalnych.

        Lucene special characters wymagające escapowania: / ( ) [ ] { } \ " ' + - * ? : ~
        Używamy whitelist approach - escapujemy tylko znane problematyczne znaki.

        Args:
            query: Oryginalny query string

        Returns:
            Sanitized query bezpieczny dla Lucene parser
        """
        # Lista znaków specjalnych Lucene wymagających escapowania
        # Źródło: https://lucene.apache.org/core/8_0_0/queryparser/org/apache/lucene/queryparser/classic/package-summary.html
        lucene_special_chars = [
            '/', '(', ')', '[', ']', '{', '}',
            '\\', '"', "'", '+', '-', '*', '?', ':', '~', '^'
        ]

        sanitized = query
        for char in lucene_special_chars:
            # Escape each special char with backslash
            # Double backslash for Python string literal
            sanitized = sanitized.replace(char, f'\\{char}')

        # Dodatkowo: usuń wielokrotne spacje (cleanup)
        import re
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()

        # Log jeśli query został zmieniony (debugging)
        if sanitized != query:
            logger.debug(
                "Lucene query sanitized: '%s' → '%s'",
                query[:100],
                sanitized[:100]
            )

        return sanitized

    async def _ensure_fulltext_index(self) -> None:
        """Tworzy indeks fulltext w Neo4j na potrzeby wyszukiwania keywordowego."""

        if not self.vector_store:
            return

        try:
            driver = self.vector_store._driver

            def check_and_create_index() -> None:
                with driver.session() as session:
                    def ensure(tx) -> None:
                        indexes = [record["name"] for record in tx.run("SHOW INDEXES")]
                        if "rag_fulltext_index" not in indexes:
                            tx.run(
                                """
                                CREATE FULLTEXT INDEX rag_fulltext_index IF NOT EXISTS
                                FOR (n:RAGChunk)
                                ON EACH [n.text]
                                """
                            )

                    session.execute_write(ensure)

            await asyncio.to_thread(check_and_create_index)
            logger.info("Fulltext index 'rag_fulltext_index' jest gotowy.")
        except Exception as exc:  # pragma: no cover - indeks nie jest krytyczny
            logger.warning("Nie udało się utworzyć indeksu fulltext: %s", exc)

    async def _keyword_search(self, query: str, k: int = 5) -> list[tuple[Document, float]]:
        """Wykonuje wyszukiwanie pełnotekstowe w Neo4j i zwraca dokumenty LangChain.

        NOWOŚĆ: Sanityzacja query (escape znaków Lucene) przed fulltext search.
        """

        if not self.vector_store:
            return []

        # Lazy initialization fulltext index przy pierwszym użyciu
        if rag.retrieval.use_hybrid_search and not self._fulltext_index_initialized:
            await self._ensure_fulltext_index()
            self._fulltext_index_initialized = True

        # SANITYZACJA: Escape znaków specjalnych Lucene przed wysłaniem query
        sanitized_query = self._sanitize_lucene_query(query)

        try:
            driver = self.vector_store._driver

            def search() -> list[tuple[Document, float]]:
                session_ctx = driver.session()
                cleanup = None

                if hasattr(session_ctx, "__enter__"):
                    session = session_ctx.__enter__()

                    def _cleanup() -> None:
                        session_ctx.__exit__(None, None, None)

                    cleanup = _cleanup
                elif hasattr(session_ctx, "__aenter__"):
                    session = session_ctx.__aenter__()
                    if asyncio.iscoroutine(session):
                        session = asyncio.run(session)

                    def _async_cleanup():
                        result = session_ctx.__aexit__(None, None, None)
                        if asyncio.iscoroutine(result):
                            asyncio.run(result)

                    cleanup = _async_cleanup
                else:
                    session = session_ctx
                    cleanup = getattr(session, "close", None)

                try:
                    result = session.run(
                        """
                        CALL db.index.fulltext.queryNodes('rag_fulltext_index', $search_query)
                        YIELD node, score
                        RETURN node.text AS text,
                               node.doc_id AS doc_id,
                               node.title AS title,
                               node.chunk_index AS chunk_index,
                               score
                        ORDER BY score DESC
                        LIMIT $limit
                        """,
                        search_query=sanitized_query,
                        limit=k,
                    )

                    records = result.data() if hasattr(result, "data") else list(result)

                    documents_with_scores: list[tuple[Document, float]] = []
                    for record in records:
                        # Obsłuż zarówno nowy format (text, doc_id, ...) jak i starszy (node -> {...})
                        if "text" in record:
                            text = record.get("text")
                            doc_id = record.get("doc_id")
                            title = record.get("title")
                            chunk_index = record.get("chunk_index")
                            score = float(record.get("score", 0.0))
                        elif "node" in record:
                            node_props = record.get("node") or {}
                            text = node_props.get("text")
                            doc_id = node_props.get("doc_id")
                            title = node_props.get("title")
                            chunk_index = node_props.get("chunk_index")
                            score = float(record.get("score", 0.0))
                        else:
                            text = None
                            doc_id = None
                            title = None
                            chunk_index = None
                            score = float(record.get("score", 0.0))

                        if not text:
                            continue

                        doc = Document(
                            page_content=text,
                            metadata={
                                "doc_id": doc_id,
                                "title": title,
                                "chunk_index": chunk_index,
                                "keyword_score": score,
                            },
                        )
                        documents_with_scores.append((doc, score))

                    return documents_with_scores
                finally:
                    try:
                        if cleanup:
                            cleanup()
                    except Exception:  # pragma: no cover - best-effort cleanup
                        pass

            documents_with_scores = await asyncio.to_thread(search)
            logger.info("Keyword search zwróciło %s wyników", len(documents_with_scores))
            return documents_with_scores
        except Exception as exc:
            # Rozróżniamy różne typy błędów dla lepszego debugowania
            error_type = type(exc).__name__

            # Lucene query syntax errors (np. nieescapowane znaki specjalne)
            if "CypherSyntaxError" in error_type or "TokenMgrError" in str(exc):
                logger.error(
                    "❌ Lucene query syntax error (prawdopodobnie znaki specjalne): %s. "
                    "Query: '%s'. Falling back to vector-only search.",
                    exc,
                    query[:100]
                )
            # Index nie istnieje lub inne błędy konfiguracji
            elif "index" in str(exc).lower() or "fulltext" in str(exc).lower():
                logger.warning(
                    "⚠️ Fulltext index niedostępny lub niepoprawnie skonfigurowany: %s. "
                    "Falling back to vector-only search.",
                    exc
                )
            # Inne błędy
            else:
                logger.warning(
                    "⚠️ Keyword search failed (%s): %s. Falling back to vector-only search.",
                    error_type,
                    exc
                )

            # Zawsze zwracamy pustą listę (graceful degradation do vector-only)
            return []

    def _format_graph_context(self, graph_nodes: list[dict[str, Any]]) -> str:
        """Formatuje węzły grafu do czytelnego kontekstu tekstowego dla LLM.

        Args:
            graph_nodes: Lista węzłów z grafu z właściwościami

        Returns:
            Sformatowany string z strukturalną wiedzą z grafu
        """
        import inspect

        # DEFENSIVE CHECK: Validate input type
        if inspect.iscoroutine(graph_nodes):
            logger.error(
                "❌ BUG: _format_graph_context received a coroutine instead of list! "
                "This indicates a serious bug in the call chain. Cleaning up and returning empty string."
            )
            graph_nodes.close()
            return ""

        if not isinstance(graph_nodes, list):
            logger.error(
                "❌ BUG: _format_graph_context received %s instead of list! "
                "Returning empty string to prevent crash",
                type(graph_nodes).__name__
            )
            return ""

        if not graph_nodes:
            return ""

        # Grupuj węzły po typie
        indicators = [n for n in graph_nodes if n.get('type') == 'Wskaznik']
        observations = [n for n in graph_nodes if n.get('type') == 'Obserwacja']
        trends = [n for n in graph_nodes if n.get('type') == 'Trend']
        demographics = [n for n in graph_nodes if n.get('type') == 'Demografia']

        sections = []

        # Sekcja Wskaźniki
        if indicators:
            sections.append("📊 WSKAŹNIKI DEMOGRAFICZNE (Wskaznik):\n")
            for ind in indicators:
                # Backward compatibility: używaj nowych nazw z fallbackiem na stare
                streszczenie = ind.get('streszczenie') or ind.get('summary', 'Brak podsumowania')
                skala = ind.get('skala') or ind.get('magnitude', 'N/A')
                pewnosc = ind.get('pewnosc') or ind.get('confidence_level', 'N/A')
                kluczowe_fakty = ind.get('kluczowe_fakty') or ind.get('key_facts', '')
                okres_czasu = ind.get('okres_czasu') or ind.get('time_period', '')

                sections.append(f"• {streszczenie}")
                if skala and skala != 'N/A':
                    sections.append(f"  Wielkość: {skala}")
                if okres_czasu:
                    sections.append(f"  Okres: {okres_czasu}")
                sections.append(f"  Pewność: {pewnosc}")
                if kluczowe_fakty:
                    sections.append(f"  Kluczowe fakty: {kluczowe_fakty}")
                sections.append("")

        # Sekcja Obserwacje
        if observations:
            sections.append("\n👥 OBSERWACJE DEMOGRAFICZNE (Obserwacja):\n")
            for obs in observations:
                # Backward compatibility: używaj nowych nazw z fallbackiem na stare
                streszczenie = obs.get('streszczenie') or obs.get('summary', 'Brak podsumowania')
                pewnosc = obs.get('pewnosc') or obs.get('confidence_level', 'N/A')
                kluczowe_fakty = obs.get('kluczowe_fakty') or obs.get('key_facts', '')
                okres_czasu = obs.get('okres_czasu') or obs.get('time_period', '')

                sections.append(f"• {streszczenie}")
                sections.append(f"  Pewność: {pewnosc}")
                if okres_czasu:
                    sections.append(f"  Okres: {okres_czasu}")
                if kluczowe_fakty:
                    sections.append(f"  Kluczowe fakty: {kluczowe_fakty}")
                sections.append("")

        # Sekcja Trendy
        if trends:
            sections.append("\n📈 TRENDY DEMOGRAFICZNE (Trend):\n")
            for trend in trends:
                # Backward compatibility: używaj nowych nazw z fallbackiem na stare
                streszczenie = trend.get('streszczenie') or trend.get('summary', 'Brak podsumowania')
                okres_czasu = trend.get('okres_czasu') or trend.get('time_period', 'N/A')
                kluczowe_fakty = trend.get('kluczowe_fakty') or trend.get('key_facts', '')

                sections.append(f"• {streszczenie}")
                sections.append(f"  Okres: {okres_czasu}")
                if kluczowe_fakty:
                    sections.append(f"  Kluczowe fakty: {kluczowe_fakty}")
                sections.append("")

        # Sekcja Demografia
        if demographics:
            sections.append("\n🎯 GRUPY DEMOGRAFICZNE (Demografia):\n")
            for demo in demographics:
                # Backward compatibility: używaj nowych nazw z fallbackiem na stare
                streszczenie = demo.get('streszczenie') or demo.get('summary', 'Brak podsumowania')
                pewnosc = demo.get('pewnosc') or demo.get('confidence_level', 'N/A')
                kluczowe_fakty = demo.get('kluczowe_fakty') or demo.get('key_facts', '')

                sections.append(f"• {streszczenie}")
                sections.append(f"  Pewność: {pewnosc}")
                if kluczowe_fakty:
                    sections.append(f"  Kluczowe fakty: {kluczowe_fakty}")
                sections.append("")

        return "\n".join(sections)

    async def _rerank_with_cross_encoder(
        self,
        query: str,
        candidates: list[tuple[Document, float]],
        top_k: int = 5
    ) -> list[tuple[Document, float]]:
        """Użyj cross-encoder aby precyzyjnie re-score query-document pairs.

        Cross-encoder ma attention mechanism który widzi query i document razem,
        co daje lepszą precision niż bi-encoder (używany w vector search).

        Args:
            query: Query użytkownika
            candidates: Lista (Document, RRF_score) par z RRF fusion
            top_k: Liczba top wyników do zwrócenia

        Returns:
            Lista (Document, rerank_score) sorted by rerank_score descending
        """
        if not self.reranker or not candidates:
            logger.info("Reranker niedostępny lub brak candidates - skip reranking")
            return candidates[:top_k]

        try:
            import time
            rerank_start = time.perf_counter()

            # Przygotuj pary (query, document) dla cross-encoder
            pairs = [(query, doc.page_content[:512]) for doc, _ in candidates]
            # Limit do 512 znaków dla cross-encoder (max_length)

            # Cross-encoder prediction - ASYNC offload to thread pool (CPU-bound task)
            # Prevents blocking event loop and disables noisy tqdm progress bar
            from functools import partial
            predict_fn = partial(
                self.reranker.predict,
                pairs,
                show_progress_bar=False,
                batch_size=16,
                num_workers=0,
            )

            # Safety timeout: if reranking is abnormally slow, fall back to RRF
            try:
                scores = await asyncio.wait_for(
                    asyncio.to_thread(predict_fn),
                    timeout=15.0,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "⏱️ Reranker timed out after 15s – using RRF scores"
                )
                return candidates[:top_k]

            # Połącz dokumenty z nowymi scores
            reranked = list(zip([doc for doc, _ in candidates], scores))

            # Sortuj po cross-encoder score (descending)
            reranked.sort(key=lambda x: x[1], reverse=True)

            rerank_duration = time.perf_counter() - rerank_start
            logger.info(
                "✅ Reranking completed: %s candidates → top %s results (%.2fs)",
                len(candidates),
                top_k,
                rerank_duration
            )

            return reranked[:top_k]

        except Exception as exc:
            logger.error("❌ Reranking failed: %s - fallback to RRF ranking", exc)
            return candidates[:top_k]

    def _find_related_graph_nodes(
        self,
        chunk_doc: Document,
        graph_nodes: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Znajdź graph nodes które są powiązane z danym chunkiem.

        Matching bazuje na:
        1. Wspólnych słowach kluczowych (z summary/key_facts)
        2. Dokumencie źródłowym (doc_id)

        Args:
            chunk_doc: Document chunk z vector/keyword search
            graph_nodes: Lista graph nodes z get_demographic_graph_context()

        Returns:
            Lista graph nodes które są powiązane z chunkiem
        """
        import inspect

        # DEFENSIVE CHECK: Validate input type
        if inspect.iscoroutine(graph_nodes):
            logger.error(
                "❌ BUG: _find_related_graph_nodes received a coroutine instead of list! "
                "Cleaning up and returning empty list."
            )
            graph_nodes.close()
            return []

        if not isinstance(graph_nodes, list):
            logger.error(
                "❌ BUG: _find_related_graph_nodes received %s instead of list!",
                type(graph_nodes).__name__
            )
            return []

        if not graph_nodes:
            return []

        related = []
        chunk_text = chunk_doc.page_content.lower()
        chunk_doc_id = chunk_doc.metadata.get('doc_id', '')

        for node in graph_nodes:
            # Sprawdź czy node pochodzi z tego samego dokumentu
            node_doc_id = node.get('doc_id', '')
            if node_doc_id and node_doc_id == chunk_doc_id:
                related.append(node)
                continue

            # Sprawdź overlap słów kluczowych
            # Backward compatibility: używaj nowych nazw z fallbackiem na stare
            summary = (node.get('streszczenie') or node.get('summary', '') or '').lower()
            key_facts = (node.get('kluczowe_fakty') or node.get('key_facts', '') or '').lower()

            # Ekstraktuj słowa kluczowe (> 5 chars)
            summary_words = {w for w in summary.split() if len(w) > 5}
            key_facts_words = {w for w in key_facts.split() if len(w) > 5}
            node_keywords = summary_words | key_facts_words

            # Policz overlap
            matches = sum(1 for keyword in node_keywords if keyword in chunk_text)

            # Jeśli >=2 matching keywords, uznaj za related
            if matches >= 2:
                related.append(node)

        return related

    def _enrich_chunk_with_graph(
        self,
        chunk_text: str,
        related_nodes: list[dict[str, Any]]
    ) -> str:
        """Wzbogać chunk o powiązane graph nodes w naturalny sposób.

        Args:
            chunk_text: Oryginalny tekst chunku
            related_nodes: Powiązane graph nodes

        Returns:
            Enriched chunk text z embedded graph context
        """
        if not related_nodes:
            return chunk_text

        # Grupuj nodes po typie
        indicators = [n for n in related_nodes if n.get('type') == 'Wskaznik']
        observations = [n for n in related_nodes if n.get('type') == 'Obserwacja']
        trends = [n for n in related_nodes if n.get('type') == 'Trend']

        enrichments = []

        # Dodaj wskaźniki
        if indicators:
            enrichments.append("\n💡 Powiązane wskaźniki:")
            for ind in indicators[:2]:  # Max 2 na chunk
                # Backward compatibility: używaj nowych nazw z fallbackiem na stare
                streszczenie = ind.get('streszczenie') or ind.get('summary', '')
                skala = ind.get('skala') or ind.get('magnitude', '')
                if streszczenie:
                    if skala:
                        enrichments.append(f"  • {streszczenie} ({skala})")
                    else:
                        enrichments.append(f"  • {streszczenie}")

        # Dodaj obserwacje
        if observations:
            enrichments.append("\n🔍 Powiązane obserwacje:")
            for obs in observations[:2]:  # Max 2 na chunk
                # Backward compatibility: używaj nowych nazw z fallbackiem na stare
                streszczenie = obs.get('streszczenie') or obs.get('summary', '')
                if streszczenie:
                    enrichments.append(f"  • {streszczenie}")

        # Dodaj trendy
        if trends:
            enrichments.append("\n📈 Powiązane trendy:")
            for trend in trends[:1]:  # Max 1 na chunk
                # Backward compatibility: używaj nowych nazw z fallbackiem na stare
                streszczenie = trend.get('streszczenie') or trend.get('summary', '')
                okres_czasu = trend.get('okres_czasu') or trend.get('time_period', '')
                if streszczenie:
                    if okres_czasu:
                        enrichments.append(f"  • {streszczenie} ({okres_czasu})")
                    else:
                        enrichments.append(f"  • {streszczenie}")

        if enrichments:
            return chunk_text + "\n" + "\n".join(enrichments)
        else:
            return chunk_text

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
        cache_key = self._get_hybrid_search_cache_key(query, top_k)
        cached_documents = await self._get_hybrid_cache(cache_key)

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

                # Vector search (timing)
                vector_start = time.perf_counter()
                vector_results = await self.vector_store.asimilarity_search_with_score(
                    query,
                    k=candidates_k,
                )
                vector_duration = time.perf_counter() - vector_start

                # Keyword search (timing)
                keyword_start = time.perf_counter()
                keyword_results = await self._keyword_search(
                    query,
                    k=candidates_k,
                )
                keyword_duration = time.perf_counter() - keyword_start

                # RRF fusion (timing)
                rrf_start = time.perf_counter()
                fused_results = self._rrf_fusion(
                    vector_results,
                    keyword_results,
                    k=rag.retrieval.rrf_k,
                )
                rrf_duration = time.perf_counter() - rrf_start

                # Optional reranking
                if rag.retrieval.use_reranking and self.reranker:
                    logger.info("Applying cross-encoder reranking")
                    final_results = await self._rerank_with_cross_encoder(
                        query=query,
                        candidates=fused_results[:rag.retrieval.rerank_candidates],
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
            await self._set_hybrid_cache(cache_key, documents)

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
                import asyncio
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
                    timeout=30,  # Default 30s timeout (RAG_GRAPH_TIMEOUT was removed)
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
                    graph_context_formatted = self._format_graph_context(graph_nodes)
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
            if rag.retrieval.use_hybrid_search:
                # Zwiększamy k aby mieć więcej candidates dla reranking
                candidates_k = rag.retrieval.rerank_candidates if rag.retrieval.use_reranking else rag.retrieval.top_k * 2

                vector_results = await self.vector_store.asimilarity_search_with_score(
                    query,
                    k=candidates_k,
                )
                keyword_results = await self._keyword_search(
                    query,
                    k=candidates_k,
                )
                fused_results = self._rrf_fusion(
                    vector_results,
                    keyword_results,
                    k=rag.retrieval.rrf_k,
                )

                # 2b. RERANKING (opcjonalne) - Precyzyjny re-scoring z cross-encoder
                if rag.retrieval.use_reranking and self.reranker:
                    logger.info("Applying cross-encoder reranking on top %s candidates", len(fused_results))
                    final_results = await self._rerank_with_cross_encoder(
                        query=query,
                        candidates=fused_results[:rag.retrieval.rerank_candidates],
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
                related_nodes = self._find_related_graph_nodes(doc, graph_nodes)

                # Wzbogać chunk jeśli są related nodes
                if related_nodes:
                    enriched_text = self._enrich_chunk_with_graph(
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

    def _rrf_fusion(
        self,
        vector_results: list[tuple[Document, float]],
        keyword_results: list[Document | tuple[Document, float]],
        k: int = 60,
    ) -> list[tuple[Document, float]]:
        """Łączy wyniki vector i keyword search przy pomocy Reciprocal Rank Fusion."""

        scores: dict[int, float] = {}
        doc_map: dict[int, tuple[Document, float]] = {}

        for rank, (doc, original_score) in enumerate(vector_results):
            doc_hash = hash(doc.page_content)
            scores[doc_hash] = scores.get(doc_hash, 0.0) + 1.0 / (k + rank + 1)
            doc_map[doc_hash] = (doc, original_score)

        for rank, item in enumerate(keyword_results):
            if isinstance(item, tuple):
                doc, keyword_score = item
            else:
                doc, keyword_score = item, 0.0

            doc_hash = hash(doc.page_content)
            scores[doc_hash] = scores.get(doc_hash, 0.0) + 1.0 / (k + rank + 1)
            if doc_hash not in doc_map:
                doc_map[doc_hash] = (doc, keyword_score)

        fused = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return [(doc_map[doc_hash][0], fused_score) for doc_hash, fused_score in fused]
