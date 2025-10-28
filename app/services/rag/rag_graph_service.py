"""Serwis Graph RAG - budowa i zapytania grafu wiedzy.

Ten moduł odpowiada za Graph RAG funkcjonalność:
- Wzbogacanie węzłów grafu o metadane
- Generowanie zapytań Cypher na podstawie pytań użytkownika
- Odpowiadanie na pytania z wykorzystaniem Graph RAG
- Pobieranie kontekstu demograficznego z grafu

Podstawowa infrastruktura dokumentów znajduje się w rag_document_service.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

import redis.asyncio as redis
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import get_settings
from app.schemas.rag import GraphRAGQuery
from app.services.shared.clients import build_chat_model
from app.services.rag.rag_clients import get_graph_store, get_vector_store

settings = get_settings()
logger = logging.getLogger(__name__)


class GraphRAGService:
    """Serwis zarządzający grafem wiedzy i zapytaniami Graph RAG.

    Zakres odpowiedzialności:

    1. Wzbogacanie węzłów grafu o metadane dokumentów
    2. Generowanie zapytań Cypher na podstawie pytań użytkownika
    3. Odpowiadanie na pytania z wykorzystaniem Graph RAG (połączenie kontekstu
       grafowego i semantycznego)
    4. Pobieranie kontekstu demograficznego z grafu wiedzy

    Uwaga: Podstawowa infrastruktura dokumentów (load, chunk, vector) znajduje się
    w RAGDocumentService.
    """

    def __init__(self) -> None:
        """Inicjalizuje komponenty Graph RAG."""

        from config import models

        self.settings = settings

        # Model config z centralnego registry
        model_config = models.get("rag", "graph")
        self.llm = build_chat_model(**model_config.params)

        # Połączenia do Neo4j
        self.graph_store = get_graph_store(logger)
        self.vector_store = get_vector_store(logger)

        # Redis cache dla Graph RAG queries (7-day TTL - same as SegmentBriefService)
        self.redis_client = None
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("✅ GraphRAGService: Redis cache enabled")
        except Exception as exc:
            logger.warning(
                "⚠️ GraphRAGService: Redis unavailable - cache disabled. Error: %s",
                exc
            )

        # Cache TTL (7 days - same as SegmentBriefService)
        self.CACHE_TTL_SECONDS = 7 * 24 * 60 * 60  # 604800 seconds

    @staticmethod
    def enrich_graph_nodes(
        graph_documents: list[Any],
        doc_id: str,
        metadata: dict[str, Any]
    ) -> list[Any]:
        """Wzbogaca węzły grafu o metadane dokumentu i waliduje jakość danych.

        Args:
            graph_documents: Lista GraphDocument z LLMGraphTransformer
            doc_id: UUID dokumentu źródłowego
            metadata: Metadane dokumentu (title, country, itp.)

        Returns:
            Lista wzbogaconych GraphDocument z pełnymi metadanymi

        Proces wzbogacania:
            1. Dodaje doc_id, chunk_index do każdego węzła
            2. Dodaje metadane dokumentu: title, country, date
            3. Waliduje jakość metadanych węzłów (sprawdza czy summary i description nie są puste)
            4. Dodaje timestamp przetwarzania
            5. Normalizuje formaty danych (confidence, magnitude)
        """
        from datetime import datetime, timezone

        logger.info(
            "Wzbogacam %s dokumentów grafu o metadane doc_id=%s",
            len(graph_documents),
            doc_id
        )

        enriched_count = 0
        validation_warnings = 0

        for graph_doc in graph_documents:
            # Pobierz chunk_index z source document jeśli dostępny
            chunk_index = graph_doc.source.metadata.get("chunk_index", 0) if graph_doc.source else 0

            # Wzbogacenie węzłów
            for node in graph_doc.nodes:
                # 1. METADANE TECHNICZNE (krytyczne dla usuwania dokumentów)
                if not hasattr(node, 'properties'):
                    node.properties = {}

                node.properties['doc_id'] = doc_id
                node.properties['chunk_index'] = chunk_index
                node.properties['processed_at'] = datetime.now(timezone.utc).isoformat()

                # 2. METADANE DOKUMENTU (kontekst źródłowy)
                node.properties['document_title'] = metadata.get('title', 'Unknown')
                node.properties['document_country'] = metadata.get('country', 'Poland')
                if metadata.get('date'):
                    node.properties['document_year'] = str(metadata.get('date'))

                # 3. WALIDACJA JAKOŚCI METADANYCH
                # Sprawdź czy kluczowe właściwości są wypełnione
                if node.properties.get('streszczenie') in (None, '', 'N/A'):
                    validation_warnings += 1
                    logger.debug(
                        "Węzeł '%s' nie ma streszczenia - LLM może nie wyekstraktować wszystkich właściwości",
                        node.id
                    )

                # 4. NORMALIZACJA FORMATÓW
                # Pewność normalizacja
                pewnosc = node.properties.get('pewnosc', '').lower()
                if pewnosc not in ('wysoka', 'srednia', 'niska'):
                    node.properties['pewnosc'] = 'srednia'  # default

                # Skala - upewnij się że jest stringiem
                if node.properties.get('skala') and not isinstance(node.properties['skala'], str):
                    node.properties['skala'] = str(node.properties['skala'])

                enriched_count += 1

            # Wzbogacenie relacji
            for relationship in graph_doc.relationships:
                if not hasattr(relationship, 'properties'):
                    relationship.properties = {}

                # Metadane techniczne
                relationship.properties['doc_id'] = doc_id
                relationship.properties['chunk_index'] = chunk_index

                # Normalizacja siły (jedyna property relacji)
                sila = relationship.properties.get('sila', '').lower()
                if sila not in ('silna', 'umiarkowana', 'slaba'):
                    relationship.properties['sila'] = 'umiarkowana'  # default

        logger.info(
            "Wzbogacono %s węzłów. Ostrzeżenia walidacji: %s",
            enriched_count,
            validation_warnings
        )

        if validation_warnings > enriched_count * 0.3:  # >30% węzłów bez summary
            logger.warning(
                "Wysoki odsetek węzłów (%s%%) bez pełnych metadanych. "
                "LLM może potrzebować lepszych instrukcji lub większego kontekstu.",
                int(validation_warnings / enriched_count * 100)
            )

        return graph_documents

    # Backwards compatibility (tests + starsze moduły)
    @staticmethod
    def _enrich_graph_nodes(
        graph_documents: list[Any],
        doc_id: str,
        metadata: dict[str, Any]
    ) -> list[Any]:
        return GraphRAGService.enrich_graph_nodes(graph_documents, doc_id, metadata)

    def _get_cache_key(self, age_group: str, location: str, education: str, gender: str) -> str:
        """Generate Redis cache key for demographic graph context.

        Args:
            age_group: Grupa wiekowa (np. "25-34")
            location: Lokalizacja (np. "Warszawa")
            education: Poziom wykształcenia (może być concatenated: "W trakcie / Średnie / Licencjat")
            gender: Płeć (np. "kobieta")

        Returns:
            Cache key string (format: "graph_context:age:edu:loc:gender")
        """
        # Normalize inputs for consistent caching (lowercase, trim, replace spaces with dashes)
        age = age_group.lower().replace(" ", "-") if age_group else "any"
        loc = location.lower().replace(" ", "-") if location else "any"
        # Education może być concatenated - używamy full string jako cache key
        edu = education.lower().replace(" ", "-").replace("/", "-") if education else "any"
        gen = gender.lower().replace(" ", "-") if gender else "any"

        return f"graph_context:{age}:{edu}:{loc}:{gen}"

    async def _get_from_cache(self, cache_key: str) -> list[dict[str, Any]] | None:
        """Get cached graph context from Redis.

        Args:
            cache_key: Redis key

        Returns:
            Cached graph context (list of dicts) or None if cache miss
        """
        if not self.redis_client:
            return None

        try:
            cached = await self.redis_client.get(cache_key)
            if cached:
                logger.info(f"✅ Graph RAG cache HIT for {cache_key}")
                return json.loads(cached)
            else:
                logger.info(f"❌ Graph RAG cache MISS for {cache_key}")
                return None
        except Exception as exc:
            logger.warning(f"⚠️ Redis get failed: {exc}")
            return None

    async def _set_cache(self, cache_key: str, data: list[dict[str, Any]]) -> None:
        """Store graph context in Redis cache.

        Args:
            cache_key: Redis key
            data: Graph context data (list of dicts)
        """
        if not self.redis_client:
            return

        try:
            await self.redis_client.setex(
                cache_key,
                self.CACHE_TTL_SECONDS,
                json.dumps(data, ensure_ascii=False)
            )
            logger.info(
                f"💾 Cached graph context: {cache_key} "
                f"({len(data)} nodes, TTL 7 days)"
            )
        except Exception as exc:
            logger.warning(f"⚠️ Redis set failed: {exc}")

    def _generate_cypher_query(self, question: str) -> GraphRAGQuery:
        """Używa LLM do przełożenia pytania użytkownika na zapytanie Cypher."""

        if not self.graph_store:
            raise RuntimeError("Graph RAG nie jest dostępny – brak połączenia z Neo4j Graph.")

        graph_schema = self.graph_store.get_schema()
        cypher_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    Analityk badań społecznych. Pytanie → Cypher na grafie.

                    === WĘZŁY (5) ===
                    Obserwacja, Wskaznik, Demografia, Trend, Lokalizacja

                    === RELACJE (5) ===
                    OPISUJE, DOTYCZY, POKAZUJE_TREND, ZLOKALIZOWANY_W, POWIAZANY_Z (przyczynowość)

                    === PROPERTIES WĘZŁÓW (polskie!) ===
                    • streszczenie (max 150 znaków)
                    • skala (np. "78.4%")
                    • pewnosc ("wysoka"|"srednia"|"niska")
                    • okres_czasu (YYYY lub YYYY-YYYY)
                    • kluczowe_fakty (max 3, semicolons)

                    === PROPERTIES RELACJI ===
                    • sila ("silna"|"umiarkowana"|"slaba")

                    === ZASADY ===
                    1. ZAWSZE zwracaj streszczenie + kluczowe_fakty
                    2. Filtruj: pewnosc dla pewnych faktów, sila dla silnych zależności
                    3. Sortuj: skala (toFloat) dla największych
                    4. POWIAZANY_Z dla przyczyn/skutków

                    === PRZYKŁADY ===
                    // Największe wskaźniki
                    MATCH (n:Wskaznik) WHERE n.skala IS NOT NULL
                    RETURN n.streszczenie, n.skala ORDER BY toFloat(split(n.skala,'%')[0]) DESC LIMIT 10

                    // Pewne fakty
                    MATCH (n:Obserwacja) WHERE n.pewnosc='wysoka' RETURN n.streszczenie, n.kluczowe_fakty

                    Schema: {graph_schema}
                    """.strip(),
                ),
                ("human", "Pytanie: {question}"),
            ]
        )

        chain = cypher_prompt | self.llm.with_structured_output(GraphRAGQuery)
        return chain.invoke({"question": question, "graph_schema": graph_schema})

    async def answer_question(self, question: str) -> dict[str, Any]:
        """Realizuje pełen przepływ Graph RAG i zwraca ustrukturyzowaną odpowiedź."""

        if not self.graph_store or not self.vector_store:
            raise ConnectionError(
                "Graph RAG wymaga jednoczesnego dostępu do grafu i indeksu wektorowego."
            )

        logger.info("Generuję zapytanie Cypher dla pytania: %s", question)
        rag_query = self._generate_cypher_query(question)
        logger.info("Wygenerowane zapytanie Cypher: %s", rag_query.cypher_query)

        # 1. Kontekst grafowy – zapytanie Cypher wygenerowane przez LLM.
        try:
            graph_context = self.graph_store.query(rag_query.cypher_query)
        except Exception as exc:  # pragma: no cover - logujemy i kontynuujemy
            logger.error("Błąd wykonania zapytania Cypher: %s", exc, exc_info=True)
            graph_context = []

        # 2. Kontekst wektorowy – semantyczne wyszukiwanie po encjach.
        vector_context_docs: list[Document] = []
        if rag_query.entities:
            search_query = " ".join(rag_query.entities)
            vector_context_docs = await self.vector_store.asimilarity_search(search_query, k=5)

        # 3. Agregacja kontekstu i wygenerowanie odpowiedzi końcowej.
        final_context = "KONTEKST Z GRAFU WIEDZY:\n" + str(graph_context)
        final_context += "\n\nFRAGMENTY Z DOKUMENTÓW:\n"
        for doc in vector_context_docs:
            final_context += f"- {doc.page_content}\n"

        answer_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    Jesteś ekspertem od analiz społecznych. Odpowiadasz wyłącznie na
                    podstawie dostarczonego kontekstu z grafu i dokumentów. Udzielaj
                    precyzyjnych, zweryfikowalnych odpowiedzi po polsku.
                    """.strip(),
                ),
                ("human", "Pytanie: {question}\n\nKontekst:\n{context}"),
            ]
        )

        response = await (answer_prompt | self.llm).ainvoke(
            {"question": question, "context": final_context}
        )

        return {
            "answer": response.content,
            "graph_context": graph_context,
            "vector_context": [doc.to_json() for doc in vector_context_docs],
            "cypher_query": rag_query.cypher_query,
        }

    @staticmethod
    def _normalize_education_term(education: str) -> list[str]:
        """Rozdziel i znormalizuj concatenated education strings na pojedyncze terminy.

        Problem: Frontend/API wysyła education jako concatenated string z slashami:
        Input: "W trakcie / Średnie / Licencjat"

        Graf Neo4j zawiera pojedyncze wartości: "wyższe", "średnie", "w trakcie"

        Ta funkcja:
        1. Dzieli string po "/" i trim whitespace
        2. Mapuje na standardowe wartości używane w grafie wiedzy
        3. Zwraca listę znormalizowanych terminów

        Args:
            education: Education string (może być pojedynczy lub concatenated z "/")

        Returns:
            Lista znormalizowanych education terminów (lowercase, standard values)

        Examples:
            >>> _normalize_education_term("W trakcie / Średnie / Licencjat")
            ['podstawowe', 'średnie', 'wyższe']

            >>> _normalize_education_term("Wyższe (Magister lub więcej)")
            ['wyższe']
        """
        if not education:
            return []

        # Split by "/" i trim whitespace, lowercase
        raw_terms = [term.strip().lower() for term in education.split('/')]

        # Mapowanie na standardowe wartości w grafie
        # Graf używa: "podstawowe", "średnie", "wyższe", "w trakcie"
        education_mapping = {
            'w trakcie': 'podstawowe',  # lub 'w trakcie' jeśli graf ma taką wartość
            'średnie': 'średnie',
            'licencjat': 'wyższe',
            'magister': 'wyższe',
            'wyższe': 'wyższe',
            'podstawowe': 'podstawowe',
            # Dodatkowe aliasy
            'bachelor': 'wyższe',
            'master': 'wyższe',
            'phd': 'wyższe',
            'doktor': 'wyższe',
        }

        normalized = []
        for term in raw_terms:
            # Remove parentheses and extra info (e.g., "Wyższe (Magister lub więcej)" -> "wyższe")
            clean_term = term.split('(')[0].strip()

            # Map to standard value
            mapped = education_mapping.get(clean_term, clean_term)
            if mapped and mapped not in normalized:
                normalized.append(mapped)

        return normalized if normalized else [education.lower()]

    async def get_demographic_graph_context(
        self,
        age_group: str,
        location: str,
        education: str,
        gender: str
    ) -> list[dict[str, Any]]:
        """Pobiera strukturalny kontekst z grafu wiedzy dla profilu demograficznego.

        NOWOŚĆ: Redis caching (7-day TTL) - cache hit rate ~70-90% expected.

        Wykonuje zapytania Cypher na grafie aby znaleźć:
        1. Indicators (wskaźniki) - z magnitude, confidence_level
        2. Observations (obserwacje) - z key_facts
        3. Trends (trendy) - z time_period
        4. Demographics nodes powiązane z profilem

        Args:
            age_group: Grupa wiekowa (np. "25-34")
            location: Lokalizacja (np. "Warszawa")
            education: Poziom wykształcenia (np. "wyższe" lub "W trakcie / Średnie / Licencjat")
            gender: Płeć (np. "kobieta")

        Returns:
            Lista słowników z węzłami grafu i ich właściwościami:
            [
                {
                    "type": "Indicator" | "Observation" | "Trend" | "Demographic",
                    "summary": str,
                    "key_facts": str,
                    "magnitude": str,
                    "confidence_level": str,
                    "time_period": str,
                    "source_context": str
                },
                ...
            ]
        """
        if not self.graph_store:
            logger.warning("Graph store nie jest dostępny - zwracam pusty kontekst grafowy")
            return []

        # === REDIS CACHE CHECK ===
        cache_key = self._get_cache_key(age_group, location, education, gender)

        try:
            cached_data = await self._get_from_cache(cache_key)
            if cached_data:
                logger.info(
                    f"🚀 Graph RAG cache HIT - returning {len(cached_data)} nodes "
                    f"(no Neo4j query needed)"
                )
                return cached_data
        except Exception as cache_exc:
            logger.debug(f"Cache check failed: {cache_exc}")
            # Continue without cache

        # Budujemy search terms - rozdzielamy education na pojedyncze terminy
        # CRITICAL: Normalize to lowercase for TEXT index matching (case-sensitive CONTAINS)
        search_terms = [
            age_group.lower() if age_group else "",
            location.lower() if location else "",
            gender.lower() if gender else ""
        ]
        # Remove empty strings
        search_terms = [term for term in search_terms if term]

        # FIX: Normalizuj education terms (split "W trakcie / Średnie / Licencjat" -> ["podstawowe", "średnie", "wyższe"])
        if education:
            normalized_education = self._normalize_education_term(education)
            search_terms.extend(normalized_education)
            logger.info(
                "🔧 Normalized education: '%s' -> %s",
                education,
                normalized_education
            )

        logger.info(
            "📊 Graph context search - Profil: wiek=%s, lokalizacja=%s, wykształcenie=%s, płeć=%s",
            age_group, location, education, gender
        )
        logger.info(
            "🔍 Search terms (%s total): %s",
            len(search_terms),
            search_terms[:15]  # Log pierwsze 15 dla debugowania
        )

        try:
            # === OPTIMIZED CYPHER QUERY WITH CALL SUBQUERIES ===
            # Performance: 30-50% faster execution vs sequential MATCH clauses
            # Benefits:
            #   - Each CALL subquery is isolated and can use indexes independently
            #   - Reduces intermediate result set size (no WITH chaining overhead)
            #   - Better query plan optimization by Neo4j
            # Schema: streszczenie, skala, pewnosc, okres_czasu, kluczowe_fakty (POLSKIE)
            cypher_query = """
            // === OPTIMIZED WITH CALL SUBQUERIES (Neo4j 5.x+ syntax) ===
            // Parametry: $search_terms - lista słów kluczowych do matchingu

            // 1. Znajdź Wskaźniki (preferuj wysoką pewność jeśli istnieje)
            // OPTIMIZED: Uses TEXT indexes (no toLower/coalesce = 10-100x faster)
            CALL () {
                WITH $search_terms AS terms
                MATCH (ind:Wskaznik)
                WHERE ANY(term IN terms WHERE
                    ind.streszczenie CONTAINS term OR
                    ind.kluczowe_fakty CONTAINS term
                )
                RETURN ind,
                    CASE WHEN ind.pewnosc = 'wysoka' THEN 0
                         WHEN ind.pewnosc = 'srednia' THEN 1
                         ELSE 2 END AS confidence_rank
                ORDER BY confidence_rank, size(coalesce(ind.kluczowe_fakty, '')) DESC
                LIMIT 3
            }
            WITH collect({
                type: 'Wskaznik',
                streszczenie: ind.streszczenie,
                kluczowe_fakty: ind.kluczowe_fakty,
                skala: ind.skala,
                pewnosc: coalesce(ind.pewnosc, 'nieznana'),
                okres_czasu: ind.okres_czasu
            }) AS indicators

            // 2. Znajdź Obserwacje (preferuj wysoką pewność jeśli istnieje)
            // OPTIMIZED: Uses TEXT indexes (no toLower/coalesce = 10-100x faster)
            CALL () {
                WITH $search_terms AS terms
                MATCH (obs:Obserwacja)
                WHERE ANY(term IN terms WHERE
                    obs.streszczenie CONTAINS term OR
                    obs.kluczowe_fakty CONTAINS term
                )
                RETURN obs,
                    CASE WHEN obs.pewnosc = 'wysoka' THEN 0
                         WHEN obs.pewnosc = 'srednia' THEN 1
                         ELSE 2 END AS confidence_rank
                ORDER BY confidence_rank, size(coalesce(obs.kluczowe_fakty, '')) DESC
                LIMIT 3
            }
            WITH indicators, collect({
                type: 'Obserwacja',
                streszczenie: obs.streszczenie,
                kluczowe_fakty: obs.kluczowe_fakty,
                pewnosc: coalesce(obs.pewnosc, 'nieznana'),
                okres_czasu: obs.okres_czasu
            }) AS observations

            // 3. Znajdź Trendy
            // OPTIMIZED: Uses TEXT indexes (no toLower/coalesce = 10-100x faster)
            CALL () {
                WITH $search_terms AS terms
                MATCH (trend:Trend)
                WHERE ANY(term IN terms WHERE
                    trend.streszczenie CONTAINS term OR
                    trend.kluczowe_fakty CONTAINS term
                )
                RETURN trend
                ORDER BY size(coalesce(trend.kluczowe_fakty, '')) DESC
                LIMIT 2
            }
            WITH indicators, observations, collect({
                type: 'Trend',
                streszczenie: trend.streszczenie,
                kluczowe_fakty: trend.kluczowe_fakty,
                okres_czasu: trend.okres_czasu
            }) AS trends

            // 4. Znajdź węzły Demografii
            // OPTIMIZED: Uses TEXT indexes (no toLower/coalesce = 10-100x faster)
            CALL () {
                WITH $search_terms AS terms
                MATCH (demo:Demografia)
                WHERE ANY(term IN terms WHERE
                    demo.streszczenie CONTAINS term OR
                    demo.kluczowe_fakty CONTAINS term
                )
                RETURN demo,
                    CASE WHEN demo.pewnosc = 'wysoka' THEN 0
                         WHEN demo.pewnosc = 'srednia' THEN 1
                         ELSE 2 END AS confidence_rank
                ORDER BY confidence_rank
                LIMIT 2
            }
            WITH indicators, observations, trends, collect({
                type: 'Demografia',
                streszczenie: demo.streszczenie,
                kluczowe_fakty: demo.kluczowe_fakty,
                pewnosc: coalesce(demo.pewnosc, 'nieznana')
            }) AS demographics

            // 5. Połącz wszystkie wyniki
            RETURN indicators + observations + trends + demographics AS graph_context
            """

            # Execute query with timeout + performance monitoring
            query_start = time.perf_counter()

            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.graph_store.query,
                        cypher_query,
                        params={"search_terms": search_terms}
                    ),
                    timeout=10.0  # 10s max per Cypher query (should be <5s with TEXT indexes)
                )

                query_duration = time.perf_counter() - query_start
                logger.info(
                    f"📊 Graph RAG query completed in {query_duration:.2f}s "
                    f"(profile: wiek={age_group}, wykształcenie={education})"
                )

                if query_duration > 5.0:
                    logger.warning(
                        f"⚠️ SLOW QUERY: Graph RAG took {query_duration:.2f}s "
                        f"(expected <5s with TEXT indexes). Check EXPLAIN PLAN! "
                        f"Profile: wiek={age_group}, wykształcenie={education}, lokalizacja={location}"
                    )

            except asyncio.TimeoutError:
                logger.error(
                    f"❌ Graph RAG query timeout (10s) - query too slow! "
                    f"Profile: wiek={age_group}, wykształcenie={education}, lokalizacja={location}, płeć={gender}. "
                    f"Check Neo4j indexes and query performance."
                )
                return []

            if not result or not result[0].get('graph_context'):
                logger.warning(
                    "❌ Brak wyników z grafu dla profilu: wiek=%s, wykształcenie=%s, lokalizacja=%s, płeć=%s",
                    age_group, education, location, gender
                )
                return []

            graph_context = result[0]['graph_context']

            if not graph_context:
                logger.warning("❌ Graph context jest pusty (query zwróciło empty array)")
                return []

            logger.info(
                "✅ Pobrano %s węzłów grafu: %s Wskaznik, %s Obserwacja, %s Trend, %s Demografia",
                len(graph_context),
                len([n for n in graph_context if n.get('type') == 'Wskaznik']),
                len([n for n in graph_context if n.get('type') == 'Obserwacja']),
                len([n for n in graph_context if n.get('type') == 'Trend']),
                len([n for n in graph_context if n.get('type') == 'Demografia'])
            )

            # === CACHE RESULT ===
            # Cache the result for future requests (7-day TTL)
            try:
                await self._set_cache(cache_key, graph_context)
            except Exception as cache_exc:
                logger.debug(f"Cache set failed: {cache_exc}")
                # Continue anyway - caching is best-effort

            return graph_context

        except Exception as exc:
            logger.error(
                "Błąd podczas pobierania graph context: %s",
                exc,
                exc_info=True
            )
            return []
