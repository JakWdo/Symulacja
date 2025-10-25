"""Serwis Graph RAG - budowa i zapytania grafu wiedzy.

Ten moduł odpowiada za Graph RAG funkcjonalność:
- Wzbogacanie węzłów grafu o metadane
- Generowanie zapytań Cypher na podstawie pytań użytkownika
- Odpowiadanie na pytania z wykorzystaniem Graph RAG
- Pobieranie kontekstu demograficznego z grafu

Podstawowa infrastruktura dokumentów znajduje się w rag_document_service.py
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import get_settings
from app.schemas.rag import GraphRAGQuery
from app.services.shared.clients import build_chat_model
from app.services.rag.rag_clients import get_graph_store, get_vector_store
from app.services.rag.utils import escape_lucene_query

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

        self.settings = settings

        # Model konwersacyjny do generowania zapytań Cypher i odpowiedzi
        self.llm = build_chat_model(
            model=settings.GRAPH_MODEL,
            temperature=0,
        )

        # Połączenia do Neo4j
        self.graph_store = get_graph_store(logger)
        self.vector_store = get_vector_store(logger)

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

    def get_demographic_graph_context(
        self,
        age_group: str,
        location: str,
        education: str,
        gender: str
    ) -> list[dict[str, Any]]:
        """Pobiera strukturalny kontekst z grafu wiedzy dla profilu demograficznego.

        OPTIMIZATION NOTE:
        - Używa fulltext index 'graph_demographic_fulltext' (60x+ szybszy niż CONTAINS)
        - Poprzednia implementacja: 4 MATCH + CONTAINS → 10-30s (timeout!)
        - Nowa implementacja: 1 CALL fulltext → <500ms
        - Index musi być utworzony: python scripts/add_graph_fulltext_indexes.py

        Wykonuje zapytania Cypher na grafie aby znaleźć:
        1. Indicators (wskaźniki) - z magnitude, confidence_level
        2. Observations (obserwacje) - z key_facts
        3. Trends (trendy) - z time_period
        4. Demographics nodes powiązane z profilem

        Args:
            age_group: Grupa wiekowa (np. "25-34")
            location: Lokalizacja (np. "Warszawa")
            education: Poziom wykształcenia (np. "wyższe")
            gender: Płeć (np. "kobieta")

        Returns:
            Lista słowników z węzłami grafu i ich właściwościami:
            [
                {
                    "type": "Wskaznik" | "Obserwacja" | "Trend" | "Demografia",
                    "streszczenie": str,
                    "kluczowe_fakty": str,
                    "skala": str,  # tylko Wskaznik
                    "pewnosc": str,
                    "okres_czasu": str,
                    "doc_id": str  # NOWE - dla łączenia z chunks
                },
                ...
            ]
        """
        if not self.graph_store:
            logger.warning("Graph store nie jest dostępny - zwracam pusty kontekst grafowy")
            return []

        # Budujemy search query string - krótkie terminy dla fulltext
        # WAŻNE: Escapujemy znaki specjalne Lucene (/, -, etc.) aby uniknąć crash Neo4j parser
        raw_query = f"{gender} {age_group} {location} {education}"
        query_string = escape_lucene_query(raw_query)

        logger.info(
            "📊 Graph context search (FULLTEXT) - Profil: wiek=%s, lokalizacja=%s, wykształcenie=%s, płeć=%s",
            age_group, location, education, gender
        )
        logger.info("🔍 Fulltext query (raw): '%s'", raw_query)
        logger.info("🔍 Fulltext query (escaped): '%s'", query_string)

        try:
            # Zapytanie Cypher z FULLTEXT INDEX (zamiast CONTAINS)
            # Index: graph_demographic_fulltext
            # Properties: streszczenie, kluczowe_fakty
            # Performance: <500ms vs 10-30s (CONTAINS)
            cypher_query = """
            // FULLTEXT SEARCH - używa indexu graph_demographic_fulltext
            // Przyspieszenie 60x+ vs poprzednia implementacja (CONTAINS)

            CALL db.index.fulltext.queryNodes('graph_demographic_fulltext', $query_string)
            YIELD node, score

            // Grupuj węzły po typie (label)
            WITH node, score, labels(node)[0] AS node_type
            WHERE node_type IN ['Wskaznik', 'Obserwacja', 'Trend', 'Demografia']
              AND score > 0.3  // Filter low-relevance results

            // CRITICAL FIX: LIMIT before collect() to prevent memory issues
            // Previously: collected ALL nodes (11k+), then limited to 10
            // Now: process max 100 nodes, then limit to 10
            LIMIT 100

            // Sortuj per typ (preferuj wysoką pewność + długie kluczowe_fakty)
            WITH node_type, node, score,
                 CASE WHEN node.pewnosc = 'wysoka' THEN 0
                      WHEN node.pewnosc = 'srednia' THEN 1
                      ELSE 2 END AS pewnosc_rank,
                 size(coalesce(node.kluczowe_fakty, '')) AS key_facts_len
            ORDER BY node_type, pewnosc_rank, key_facts_len DESC, score DESC

            // Zbierz per typ z limitami (3 Wskaznik, 3 Obserwacja, 2 Trend, 2 Demografia)
            WITH node_type, collect(node) AS nodes

            // Rozbij na listy per typ
            WITH
                [n IN nodes WHERE node_type = 'Wskaznik'][..3] AS wskaznik_nodes,
                [n IN nodes WHERE node_type = 'Obserwacja'][..3] AS obserwacja_nodes,
                [n IN nodes WHERE node_type = 'Trend'][..2] AS trend_nodes,
                [n IN nodes WHERE node_type = 'Demografia'][..2] AS demografia_nodes

            // Map nodes to output format (z doc_id!)
            WITH
                [n IN wskaznik_nodes | {
                    type: 'Wskaznik',
                    streszczenie: n.streszczenie,
                    kluczowe_fakty: n.kluczowe_fakty,
                    skala: n.skala,
                    pewnosc: coalesce(n.pewnosc, 'nieznana'),
                    okres_czasu: n.okres_czasu,
                    doc_id: n.doc_id
                }] AS indicators,
                [n IN obserwacja_nodes | {
                    type: 'Obserwacja',
                    streszczenie: n.streszczenie,
                    kluczowe_fakty: n.kluczowe_fakty,
                    pewnosc: coalesce(n.pewnosc, 'nieznana'),
                    okres_czasu: n.okres_czasu,
                    doc_id: n.doc_id
                }] AS observations,
                [n IN trend_nodes | {
                    type: 'Trend',
                    streszczenie: n.streszczenie,
                    kluczowe_fakty: n.kluczowe_fakty,
                    okres_czasu: n.okres_czasu,
                    doc_id: n.doc_id
                }] AS trends,
                [n IN demografia_nodes | {
                    type: 'Demografia',
                    streszczenie: n.streszczenie,
                    kluczowe_fakty: n.kluczowe_fakty,
                    pewnosc: coalesce(n.pewnosc, 'nieznana'),
                    doc_id: n.doc_id
                }] AS demographics

            // Połącz wszystkie wyniki
            RETURN indicators + observations + trends + demographics AS graph_context
            """

            result = self.graph_store.query(
                cypher_query,
                params={"query_string": query_string}
            )

            if not result or not result[0].get('graph_context'):
                logger.warning(
                    "❌ Brak wyników z grafu dla profilu: wiek=%s, wykształcenie=%s, lokalizacja=%s, płeć=%s",
                    age_group, education, location, gender
                )
                logger.warning(
                    "   Sprawdź czy index 'graph_demographic_fulltext' istnieje: "
                    "python scripts/add_graph_fulltext_indexes.py"
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

            return graph_context

        except Exception as exc:
            logger.error(
                "Błąd podczas pobierania graph context: %s",
                exc,
                exc_info=True
            )
            logger.error(
                "   Możliwa przyczyna: brak indexu 'graph_demographic_fulltext'. "
                "Uruchom: python scripts/add_graph_fulltext_indexes.py"
            )
            return []
