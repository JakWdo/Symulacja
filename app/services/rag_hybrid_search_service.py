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
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain_core.documents import Document
from langchain_experimental.graph_transformers.llm import LLMGraphTransformer
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings
from app.models.rag_document import RAGDocument

settings = get_settings()
logger = logging.getLogger(__name__)


class PolishSocietyRAG:
    """Hybrydowe wyszukiwanie kontekstu dla generatora person.

    Łączy wyszukiwanie semantyczne (embeddingi) oraz pełnotekstowe (fulltext index)
    korzystając z techniki Reciprocal Rank Fusion. Klasa jest niezależna od
    Graph RAG, ale współdzieli te same ustawienia i konwencję metadanych.
    """

    def __init__(self) -> None:
        """Przygotowuje wektorowe i keywordowe zaplecze wyszukiwawcze."""

        self.settings = settings

        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
        )

        # Inicjalizacja Neo4j Vector Store z retry logic (dla Docker startup race condition)
        self.vector_store = self._init_vector_store_with_retry()

        if self.vector_store:
            logger.info("✅ PolishSocietyRAG: Neo4j Vector Store połączony")

            # Fulltext index będzie tworzony lazy - przy pierwszym użyciu keyword search
            # (nie możemy użyć asyncio.create_task() w __init__ bo może nie być event loop)
            self._fulltext_index_initialized = False

            # Leniwa inicjalizacja GraphRAGService dla dostępu do kontekstu grafowego
            self._graph_rag_service = None

            # Inicjalizuj cross-encoder dla reranking (opcjonalny)
            self.reranker = None
            if settings.RAG_USE_RERANKING:
                try:
                    from sentence_transformers import CrossEncoder
                    self.reranker = CrossEncoder(
                        settings.RAG_RERANKER_MODEL,
                        max_length=512
                    )
                    logger.info(
                        "Cross-encoder reranker zainicjalizowany: %s",
                        settings.RAG_RERANKER_MODEL
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

    def _init_vector_store_with_retry(self, max_retries: int = 10, initial_delay: float = 1.0):
        """Inicjalizuje Neo4j Vector Store z retry logic (dla Docker startup).

        Neo4j w Dockerze potrzebuje 10-15s na start (plugins: APOC, GDS).
        Retry z exponential backoff zapobiega race condition przy startup.

        Args:
            max_retries: Maksymalna liczba prób (default: 10 = ~30s total)
            initial_delay: Początkowe opóźnienie w sekundach (default: 1.0s)

        Returns:
            Neo4jVector instance lub None jeśli wszystkie próby failed
        """
        import time

        logger.info("🔄 PolishSocietyRAG: Inicjalizacja Neo4j Vector Store (z retry logic)")

        delay = initial_delay
        for attempt in range(1, max_retries + 1):
            try:
                vector_store = Neo4jVector(
                    url=settings.NEO4J_URI,
                    username=settings.NEO4J_USER,
                    password=settings.NEO4J_PASSWORD,
                    embedding=self.embeddings,
                    index_name="rag_document_embeddings",
                    node_label="RAGChunk",
                    text_node_property="text",
                    embedding_node_property="embedding",
                )
                logger.info("✅ PolishSocietyRAG: Neo4j Vector Store połączony (próba %d/%d)", attempt, max_retries)
                return vector_store

            except Exception as exc:
                if attempt < max_retries:
                    logger.warning(
                        "⚠️  PolishSocietyRAG: Neo4j Vector Store - próba %d/%d failed: %s. Retry za %.1fs...",
                        attempt, max_retries, str(exc)[:100], delay
                    )
                    time.sleep(delay)
                    delay = min(delay * 1.5, 10.0)  # Exponential backoff (cap at 10s)
                else:
                    logger.error(
                        "❌ PolishSocietyRAG: Neo4j Vector Store - wszystkie %d prób failed",
                        max_retries,
                        exc_info=True
                    )
                    return None

        return None

    @property
    def graph_rag_service(self):
        """Leniwa inicjalizacja GraphRAGService dla dostępu do strukturalnego kontekstu."""
        if self._graph_rag_service is None:
            from app.services.rag_graph_service import GraphRAGService

            self._graph_rag_service = GraphRAGService()
        return self._graph_rag_service

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

    async def _keyword_search(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """Wykonuje wyszukiwanie pełnotekstowe w Neo4j i zwraca dokumenty LangChain."""

        if not self.vector_store:
            return []

        # Lazy initialization fulltext index przy pierwszym użyciu
        if settings.RAG_USE_HYBRID_SEARCH and not self._fulltext_index_initialized:
            await self._ensure_fulltext_index()
            self._fulltext_index_initialized = True

        try:
            driver = self.vector_store._driver

            def search() -> List[Tuple[Document, float]]:
                session_ctx = driver.session()
                cleanup = None

                if hasattr(session_ctx, "__enter__"):
                    session = session_ctx.__enter__()
                    cleanup = lambda: session_ctx.__exit__(None, None, None)
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
                        search_query=query,
                        limit=k,
                    )

                    records = result.data() if hasattr(result, "data") else list(result)

                    documents_with_scores: List[Tuple[Document, float]] = []
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
        except Exception as exc:  # pragma: no cover - fallback do vector search
            logger.warning("Keyword search nie powiodło się, używam fallbacku: %s", exc)
            return []

    def _format_graph_context(self, graph_nodes: List[Dict[str, Any]]) -> str:
        """Formatuje węzły grafu do czytelnego kontekstu tekstowego dla LLM.

        Args:
            graph_nodes: Lista węzłów z grafu z właściwościami

        Returns:
            Sformatowany string z strukturalną wiedzą z grafu
        """
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

    def _rerank_with_cross_encoder(
        self,
        query: str,
        candidates: List[Tuple[Document, float]],
        top_k: int = 5
    ) -> List[Tuple[Document, float]]:
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
            # Przygotuj pary (query, document) dla cross-encoder
            pairs = [(query, doc.page_content[:512]) for doc, _ in candidates]
            # Limit do 512 znaków dla cross-encoder (max_length)

            # Cross-encoder prediction (sync, ale szybkie ~100-200ms dla 20 docs)
            scores = self.reranker.predict(pairs)

            # Połącz dokumenty z nowymi scores
            reranked = list(zip([doc for doc, _ in candidates], scores))

            # Sortuj po cross-encoder score (descending)
            reranked.sort(key=lambda x: x[1], reverse=True)

            logger.info(
                "Reranking completed: %s candidates → top %s results",
                len(candidates),
                top_k
            )

            return reranked[:top_k]

        except Exception as exc:
            logger.error("Reranking failed: %s - fallback to RRF ranking", exc)
            return candidates[:top_k]

    def _find_related_graph_nodes(
        self,
        chunk_doc: Document,
        graph_nodes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
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
        related_nodes: List[Dict[str, Any]]
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
    ) -> List[Document]:
        """Wykonuje hybrydowe wyszukiwanie (vector + keyword + RRF fusion).

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

        logger.info("Hybrid search: query='%s...', top_k=%s", query[:50], top_k)

        try:
            # HYBRID SEARCH (Vector + Keyword)
            if settings.RAG_USE_HYBRID_SEARCH:
                # Zwiększamy k aby mieć więcej candidates dla reranking
                candidates_k = settings.RAG_RERANK_CANDIDATES if settings.RAG_USE_RERANKING else top_k * 2

                # Vector search
                vector_results = await self.vector_store.asimilarity_search_with_score(
                    query,
                    k=candidates_k,
                )

                # Keyword search
                keyword_results = await self._keyword_search(
                    query,
                    k=candidates_k,
                )

                # RRF fusion
                fused_results = self._rrf_fusion(
                    vector_results,
                    keyword_results,
                    k=settings.RAG_RRF_K,
                )

                # Optional reranking
                if settings.RAG_USE_RERANKING and self.reranker:
                    logger.info("Applying cross-encoder reranking")
                    final_results = self._rerank_with_cross_encoder(
                        query=query,
                        candidates=fused_results[:settings.RAG_RERANK_CANDIDATES],
                        top_k=top_k
                    )
                else:
                    final_results = fused_results[:top_k]
            else:
                # Vector-only search
                final_results = await self.vector_store.asimilarity_search_with_score(
                    query,
                    k=top_k,
                )

            # Return only Documents (strip scores)
            documents = [doc for doc, score in final_results]
            logger.info("Hybrid search returned %s documents", len(documents))
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
    ) -> Dict[str, Any]:
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
                graph_nodes = self.graph_rag_service.get_demographic_graph_context(
                    age_group=age_group,
                    location=location,
                    education=education,
                    gender=gender
                )
                if graph_nodes:
                    graph_context_formatted = self._format_graph_context(graph_nodes)
                    logger.info("Pobrano %s węzłów grafu z kontekstem demograficznym", len(graph_nodes))
                else:
                    logger.info("Brak wyników z graph context dla podanego profilu")
            except Exception as graph_exc:
                logger.warning("Nie udało się pobrać graph context: %s", graph_exc)

            # 2. HYBRID SEARCH (Vector + Keyword) - Pobierz chunki tekstowe
            if settings.RAG_USE_HYBRID_SEARCH:
                # Zwiększamy k aby mieć więcej candidates dla reranking
                candidates_k = settings.RAG_RERANK_CANDIDATES if settings.RAG_USE_RERANKING else settings.RAG_TOP_K * 2

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
                    k=settings.RAG_RRF_K,
                )

                # 2b. RERANKING (opcjonalne) - Precyzyjny re-scoring z cross-encoder
                if settings.RAG_USE_RERANKING and self.reranker:
                    logger.info("Applying cross-encoder reranking on top %s candidates", len(fused_results))
                    final_results = self._rerank_with_cross_encoder(
                        query=query,
                        candidates=fused_results[:settings.RAG_RERANK_CANDIDATES],
                        top_k=settings.RAG_TOP_K
                    )
                    search_type = "hybrid+rerank+graph" if graph_nodes else "hybrid+rerank"
                else:
                    final_results = fused_results[:settings.RAG_TOP_K]
                    search_type = "hybrid+graph" if graph_nodes else "hybrid"
            else:
                final_results = await self.vector_store.asimilarity_search_with_score(
                    query,
                    k=settings.RAG_TOP_K,
                )
                search_type = "vector_only+graph" if graph_nodes else "vector_only"

            # 3. UNIFIED CONTEXT - Wzbogać chunki o powiązane graph nodes
            context_chunks: List[str] = []
            citations: List[Dict[str, Any]] = []
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
            if len(context) > settings.RAG_MAX_CONTEXT_CHARS:
                context = context[: settings.RAG_MAX_CONTEXT_CHARS] + "\n\n[... kontekst obcięty]"

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
        vector_results: List[Tuple[Document, float]],
        keyword_results: List[Union[Document, Tuple[Document, float]]],
        k: int = 60,
    ) -> List[Tuple[Document, float]]:
        """Łączy wyniki vector i keyword search przy pomocy Reciprocal Rank Fusion."""

        scores: Dict[int, float] = {}
        doc_map: Dict[int, Tuple[Document, float]] = {}

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
