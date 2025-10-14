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
from typing import Any, Dict, List, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_experimental.graph_transformers.llm import LLMGraphTransformer
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings
from app.models.rag_document import RAGDocument

settings = get_settings()
logger = logging.getLogger(__name__)


class GraphRAGQuery(BaseModel):
    """Struktura odpowiedzi z LLM przekształcająca pytanie w zapytanie Cypher."""

    entities: List[str] = Field(
        default_factory=list,
        description="Lista najważniejszych encji z pytania użytkownika.",
    )
    cypher_query: str = Field(
        description="Zapytanie Cypher, które ma zostać wykonane na grafie wiedzy.",
    )


class RAGDocumentService:
    """Serwis zarządzający dokumentami, grafem wiedzy i zapytaniami Graph RAG.

    Zakres odpowiedzialności:

    1. Wczytywanie dokumentów PDF/DOCX i dzielenie ich na fragmenty.
    2. Generowanie embeddingów i zapis chunków w indeksie wektorowym Neo4j.
    3. Budowa uniwersalnego grafu wiedzy na bazie `LLMGraphTransformer`.
    4. Odpowiadanie na pytania użytkowników z wykorzystaniem Graph RAG
       (połączenie kontekstu grafowego i semantycznego).
    5. Zarządzanie dokumentami w bazie PostgreSQL (lista, usuwanie z czyszczeniem
       danych w Neo4j).
    """

    def __init__(self) -> None:
        """Inicjalizuje wszystkie niezbędne komponenty LangChain i Neo4j."""

        self.settings = settings

        # Model konwersacyjny wykorzystywany zarówno do budowy grafu, jak i
        # generowania finalnych odpowiedzi Graph RAG.
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GRAPH_MODEL,
            google_api_key=self.settings.GOOGLE_API_KEY,
            temperature=0,
        )

        # Embeddingi Google Gemini wykorzystywane przez indeks wektorowy Neo4j.
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
        )

        # Inicjalizacja Neo4j Vector Store z retry logic (dla Docker startup race condition)
        self.vector_store = self._init_vector_store_with_retry()

        # Inicjalizacja Neo4j Graph Store z retry logic
        self.graph_store = self._init_graph_store_with_retry()

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

        logger.info("🔄 Inicjalizacja Neo4j Vector Store (z retry logic)")
        logger.info("   URL: %s, User: %s", settings.NEO4J_URI, settings.NEO4J_USER)

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
                logger.info("✅ Neo4j Vector Store połączony (próba %d/%d)", attempt, max_retries)
                return vector_store

            except Exception as exc:
                if attempt < max_retries:
                    logger.warning(
                        "⚠️  Neo4j Vector Store - próba %d/%d failed: %s. Retry za %.1fs...",
                        attempt, max_retries, str(exc)[:100], delay
                    )
                    time.sleep(delay)
                    delay = min(delay * 1.5, 10.0)  # Exponential backoff (cap at 10s)
                else:
                    logger.error(
                        "❌ Neo4j Vector Store - wszystkie %d prób failed. RAG wyłączony.",
                        max_retries,
                        exc_info=True
                    )
                    return None

        return None

    def _init_graph_store_with_retry(self, max_retries: int = 10, initial_delay: float = 1.0):
        """Inicjalizuje Neo4j Graph Store z retry logic (dla Docker startup).

        Args:
            max_retries: Maksymalna liczba prób (default: 10 = ~30s total)
            initial_delay: Początkowe opóźnienie w sekundach (default: 1.0s)

        Returns:
            Neo4jGraph instance lub None jeśli wszystkie próby failed
        """
        import time

        logger.info("🔄 Inicjalizacja Neo4j Graph Store (z retry logic)")

        delay = initial_delay
        for attempt in range(1, max_retries + 1):
            try:
                graph_store = Neo4jGraph(
                    url=settings.NEO4J_URI,
                    username=settings.NEO4J_USER,
                    password=settings.NEO4J_PASSWORD,
                )
                logger.info("✅ Neo4j Graph Store połączony (próba %d/%d)", attempt, max_retries)
                return graph_store

            except Exception as exc:
                if attempt < max_retries:
                    logger.warning(
                        "⚠️  Neo4j Graph Store - próba %d/%d failed: %s. Retry za %.1fs...",
                        attempt, max_retries, str(exc)[:100], delay
                    )
                    time.sleep(delay)
                    delay = min(delay * 1.5, 10.0)  # Exponential backoff (cap at 10s)
                else:
                    logger.error(
                        "❌ Neo4j Graph Store - wszystkie %d prób failed. GraphRAG wyłączony.",
                        max_retries,
                        exc_info=True
                    )
                    return None

        return None

    async def ingest_document(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Przetwarza dokument przez pełny pipeline: load → chunk → graph → vector.

        Args:
            file_path: Ścieżka do pliku PDF lub DOCX zapisanej kopii dokumentu.
            metadata: Metadane dokumentu (doc_id, title, country, itp.).

        Returns:
            Słownik zawierający liczbę chunków oraz status zakończenia procesu.

        Raises:
            RuntimeError: Gdy brakuje połączenia z Neo4j (vector store jest kluczowy).
            FileNotFoundError: Jeśli plik nie istnieje.
            ValueError: Przy nieobsługiwanym rozszerzeniu lub braku treści.
        """

        if not self.vector_store:
            raise RuntimeError("Brak połączenia z Neo4j Vector Store – ingest niemożliwy.")

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Nie znaleziono pliku: {file_path}")

        logger.info("Rozpoczynam przetwarzanie dokumentu: %s", path.name)

        try:
            # 1. LOAD – wybór loadera zależnie od rozszerzenia pliku.
            file_extension = path.suffix.lower()
            if file_extension == ".pdf":
                loader = PyPDFLoader(str(path))
                logger.info("Używam PyPDFLoader dla pliku %s", path.name)
            elif file_extension == ".docx":
                loader = Docx2txtLoader(str(path))
                logger.info("Używam Docx2txtLoader dla pliku %s", path.name)
            else:
                raise ValueError(
                    f"Nieobsługiwany typ pliku: {file_extension}. Dozwolone: PDF, DOCX."
                )

            documents = await asyncio.to_thread(loader.load)
            if not documents:
                raise ValueError("Nie udało się odczytać zawartości dokumentu.")
            logger.info("Wczytano %s segmentów dokumentu źródłowego.", len(documents))

            # 2. SPLIT – dzielenie tekstu na fragmenty z kontrolowanym overlapem.
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.RAG_CHUNK_SIZE,
                chunk_overlap=settings.RAG_CHUNK_OVERLAP,
                separators=["\n\n", "\n", ". ", " ", ""],
                length_function=len,
            )
            chunks = text_splitter.split_documents(documents)
            if not chunks:
                raise ValueError("Nie wygenerowano żadnych fragmentów tekstu.")
            logger.info(
                "Podzielono dokument na %s fragmentów (chunk_size=%s, overlap=%s)",
                len(chunks),
                settings.RAG_CHUNK_SIZE,
                settings.RAG_CHUNK_OVERLAP,
            )

            # 3. METADATA – wzbogacenie każdego chunku o metadane identyfikujące.
            doc_id = metadata.get("doc_id")
            for index, chunk in enumerate(chunks):
                chunk.metadata.update(
                    {
                        "doc_id": str(doc_id),
                        "chunk_index": index,
                        "title": metadata.get("title", "Nieznany dokument"),
                        "country": metadata.get("country", "Poland"),
                        "source_file": path.name,
                    }
                )

            # 4. GRAPH – próbujemy zbudować graf wiedzy, jeśli Neo4j Graph jest dostępny.
            if self.graph_store:
                try:
                    logger.info("Generuję strukturę grafową na podstawie uniwersalnego modelu.")
                    transformer = LLMGraphTransformer(
                        llm=self.llm,
                        allowed_nodes=[
                            "Obserwacja",   # Fakty, obserwacje (merge Przyczyna, Skutek tutaj)
                            "Wskaznik",     # Wskaźniki liczbowe, statystyki
                            "Demografia",   # Grupy demograficzne
                            "Trend",        # Trendy czasowe, zmiany w czasie
                            "Lokalizacja",  # Miejsca geograficzne
                        ],
                        allowed_relationships=[
                            "OPISUJE",           # Opisuje cechę/właściwość
                            "DOTYCZY",           # Dotyczy grupy/kategorii
                            "POKAZUJE_TREND",    # Pokazuje trend czasowy
                            "ZLOKALIZOWANY_W",   # Zlokalizowane w miejscu
                            "POWIAZANY_Z",       # Ogólne powiązanie (merge: przyczynowość, porównania)
                        ],
                        node_properties=[
                            "streszczenie",     # MUST: Jednozdaniowe podsumowanie (max 150 znaków)
                            "skala",            # Wielkość/wartość z jednostką (np. "67%", "1.2 mln")
                            "pewnosc",          # MUST: Pewność: "wysoka", "srednia", "niska"
                            "okres_czasu",      # Okres czasu (YYYY lub YYYY-YYYY)
                            "kluczowe_fakty",   # Opcjonalnie: max 3 fakty (separated by semicolons)
                        ],
                        relationship_properties=[
                            "sila",  # Siła relacji: "silna", "umiarkowana", "slaba"
                        ],
                        additional_instructions="""
JĘZYK: Wszystkie nazwy i wartości MUSZĄ być PO POLSKU.

=== TYPY WĘZŁÓW (5) ===
- Obserwacja: Fakty, obserwacje społeczne (włącznie z przyczynami i skutkami)
- Wskaznik: Wskaźniki liczbowe, statystyki (np. stopa zatrudnienia)
- Demografia: Grupy demograficzne (np. młodzi dorośli)
- Trend: Trendy czasowe, zmiany w czasie
- Lokalizacja: Miejsca geograficzne

=== TYPY RELACJI (5) ===
- OPISUJE: Opisuje cechę/właściwość
- DOTYCZY: Dotyczy grupy/kategorii
- POKAZUJE_TREND: Pokazuje trend czasowy
- ZLOKALIZOWANY_W: Zlokalizowane w miejscu
- POWIAZANY_Z: Ogólne powiązanie (przyczynowość, porównania, korelacje)

=== PROPERTIES WĘZŁÓW (5 - uproszczone!) ===
- streszczenie (MUST): 1 zdanie, max 150 znaków
- skala: Wartość z jednostką (np. "78.4%", "5000 PLN", "1.2 mln osób")
- pewnosc (MUST): "wysoka" / "srednia" / "niska"
- okres_czasu: YYYY lub YYYY-YYYY
- kluczowe_fakty: Max 3 fakty oddzielone średnikami

=== PROPERTIES RELACJI (1) ===
- sila: "silna" / "umiarkowana" / "slaba"

=== PRZYKŁADY (FEW-SHOT) ===

PRZYKŁAD 1 - Wskaznik:
Tekst: "W 2022 stopa zatrudnienia kobiet 25-34 z wyższym wynosiła 78.4% według GUS"
Węzeł: {{
  type: "Wskaznik",
  streszczenie: "Stopa zatrudnienia kobiet 25-34 z wyższym wykształceniem",
  skala: "78.4%",
  pewnosc: "wysoka",
  okres_czasu: "2022",
  kluczowe_fakty: "wysoka stopa zatrudnienia; kobiety młode; wykształcenie wyższe"
}}

PRZYKŁAD 2 - Obserwacja:
Tekst: "Młodzi mieszkańcy dużych miast coraz częściej wynajmują mieszkania zamiast kupować"
Węzeł: {{
  type: "Obserwacja",
  streszczenie: "Młodzi w miastach preferują wynajem nad zakup mieszkań",
  pewnosc: "srednia",
  kluczowe_fakty: "młodzi dorośli; duże miasta; wynajem mieszkań"
}}

PRZYKŁAD 3 - Trend:
Tekst: "Od 2018 do 2023 wzrósł odsetek osób pracujących zdalnie z 12% do 31%"
Węzeł: {{
  type: "Trend",
  streszczenie: "Wzrost pracy zdalnej w Polsce",
  skala: "12% → 31%",
  pewnosc: "wysoka",
  okres_czasu: "2018-2023",
  kluczowe_fakty: "praca zdalna; wzrost; pandemia"
}}

=== VALIDATION RULES ===
- streszczenie: Zawsze wypełnij (1 zdanie, max 150 znaków)
- pewnosc: Zawsze wypełnij ("wysoka", "srednia", "niska")
- skala: Tylko dla Wskaznik (inne: opcjonalnie)
- kluczowe_fakty: Max 3 fakty, separated by semicolons
- doc_id, chunk_index: KRYTYCZNE dla lifecycle (zachowane automatycznie)

=== FOCUS ===
Priorytet: streszczenie + pewnosc. Nie trać czasu na zbędne opisy.
                        """.strip(),
                    )
                    graph_documents = await transformer.aconvert_to_graph_documents(chunks)

                    # Wzbogacenie węzłów o metadane dokumentu
                    enriched_graph_documents = self._enrich_graph_nodes(
                        graph_documents,
                        doc_id=str(doc_id),
                        metadata=metadata
                    )

                    self.graph_store.add_graph_documents(enriched_graph_documents, include_source=True)
                    logger.info("Zapisano strukturę grafową dla dokumentu %s", doc_id)
                except Exception as graph_exc:  # pragma: no cover - logujemy, ale nie przerywamy
                    logger.error(
                        "Nie udało się wygenerować grafu wiedzy dla dokumentu %s: %s",
                        doc_id,
                        graph_exc,
                        exc_info=True,
                    )

            else:
                logger.warning(
                    "Neo4j Graph Store nie jest dostępny – dokument zostanie przetworzony "
                    "bez struktury grafowej."
                )

            # 5. VECTOR – zapis chunków do indeksu wektorowego w Neo4j.
            logger.info("Generuję embeddingi i zapisuję je w indeksie wektorowym...")
            await self.vector_store.aadd_documents(chunks)
            logger.info(
                "Zakończono przetwarzanie %s fragmentów dokumentu %s",
                len(chunks),
                doc_id,
            )

            return {"num_chunks": len(chunks), "status": "ready"}

        except Exception as exc:  # pragma: no cover - logujemy pełną diagnostykę
            logger.error(
                "Błąd podczas przetwarzania dokumentu %s: %s",
                file_path,
                exc,
                exc_info=True,
            )
            return {"num_chunks": 0, "status": "failed", "error": str(exc)}

    def _enrich_graph_nodes(
        self,
        graph_documents: List[Any],
        doc_id: str,
        metadata: Dict[str, Any]
    ) -> List[Any]:
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
                    Jesteś analitykiem badań społecznych. Twoim zadaniem jest zamiana pytania
                    użytkownika na zapytanie Cypher korzystające z poniższego schematu grafu.

                    === DOSTĘPNE TYPY WĘZŁÓW (5) ===
                    - Obserwacja: Fakty, obserwacje (włącznie z przyczynami i skutkami)
                    - Wskaznik: Wskaźniki liczbowe, statystyki
                    - Demografia: Grupy demograficzne
                    - Trend: Trendy czasowe
                    - Lokalizacja: Miejsca geograficzne

                    === DOSTĘPNE TYPY RELACJI (5) ===
                    - OPISUJE, DOTYCZY, POKAZUJE_TREND, ZLOKALIZOWANY_W
                    - POWIAZANY_Z: Ogólne powiązanie (przyczynowość, porównania)

                    === DOSTĘPNE WŁAŚCIWOŚCI WĘZŁÓW (5 - uproszczone!) ===
                    - streszczenie: Jednozdaniowe podsumowanie (max 150 znaków)
                    - skala: Wielkość/wartość z jednostką (np. "78.4%")
                    - pewnosc: Pewność danych ("wysoka", "srednia", "niska")
                    - okres_czasu: Okres czasu (YYYY lub YYYY-YYYY)
                    - kluczowe_fakty: Max 3 fakty (separated by semicolons)
                    - document_title, document_country, document_year: Metadane dokumentu

                    === DOSTĘPNE WŁAŚCIWOŚCI RELACJI (1) ===
                    - sila: Siła relacji ("silna", "umiarkowana", "slaba")

                    === INSTRUKCJE TWORZENIA ZAPYTAŃ ===
                    1. Używaj POLSKICH nazw properties (streszczenie, pewnosc, skala, etc.)
                    2. ZAWSZE zwracaj streszczenie + kluczowe_fakty
                    3. Filtruj po pewnosc jeśli użytkownik pyta o pewne fakty ("wysoka")
                    4. Filtruj po sila relacji dla silnych zależności ("silna")
                    5. Sortuj po skala dla pytań o największe wskaźniki
                    6. Filtruj po okres_czasu dla pytań czasowych
                    7. Używaj POWIAZANY_Z dla pytań o zależności/przyczyny

                    === PRZYKŁADY ZAPYTAŃ (nowy schema) ===
                    ```cypher
                    // Największe wskaźniki
                    MATCH (n:Wskaznik) WHERE n.skala IS NOT NULL
                    RETURN n.streszczenie, n.skala, n.pewnosc, n.okres_czasu
                    ORDER BY toFloat(split(n.skala, '%')[0]) DESC LIMIT 10

                    // Pewne fakty o X
                    MATCH (n:Obserwacja)
                    WHERE n.streszczenie CONTAINS 'X' AND n.pewnosc = 'wysoka'
                    RETURN n.streszczenie, n.kluczowe_fakty, n.okres_czasu

                    // Powiązania X → Y (używa POWIAZANY_Z)
                    MATCH (n1)-[r:POWIAZANY_Z]->(n2)
                    WHERE n1.streszczenie CONTAINS 'X' AND r.sila = 'silna'
                    RETURN n1.streszczenie, r.sila, n2.streszczenie
                    ```

                    Schemat grafu: {graph_schema}
                    """.strip(),
                ),
                ("human", "Pytanie użytkownika: {question}"),
            ]
        )

        chain = cypher_prompt | self.llm.with_structured_output(GraphRAGQuery)
        return chain.invoke({"question": question, "graph_schema": graph_schema})

    async def answer_question(self, question: str) -> Dict[str, Any]:
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
        vector_context_docs: List[Document] = []
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

    async def list_documents(self, db: AsyncSession) -> List[RAGDocument]:
        """Zwraca listę aktywnych dokumentów posortowanych malejąco po dacie."""

        result = await db.execute(
            select(RAGDocument)
            .where(RAGDocument.is_active.is_(True))
            .order_by(RAGDocument.created_at.desc())
        )
        return result.scalars().all()

    async def delete_document(self, doc_id: UUID, db: AsyncSession) -> None:
        """Usuwa dokument z PostgreSQL i czyści powiązane dane w Neo4j."""

        doc = await db.get(RAGDocument, doc_id)
        if not doc:
            raise ValueError(f"Document {doc_id} not found")

        doc.is_active = False
        await db.commit()

        await self._delete_chunks_from_neo4j(str(doc_id))

        if self.graph_store:
            try:
                self.graph_store.query(
                    "MATCH (n {doc_id: $doc_id}) DETACH DELETE n",
                    params={"doc_id": str(doc_id)},
                )
                logger.info("Usunięto węzły grafu dla dokumentu %s", doc_id)
            except Exception as exc:  # pragma: no cover - logujemy, ale nie przerywamy
                logger.error(
                    "Nie udało się usunąć węzłów grafu dokumentu %s: %s",
                    doc_id,
                    exc,
                )

    async def _delete_chunks_from_neo4j(self, doc_id: str) -> None:
        """Czyści wszystkie chunki dokumentu z indeksu Neo4j Vector."""

        if not self.vector_store:
            return

        try:
            driver = self.vector_store._driver  # Dostęp wewnętrzny – akceptowalny w serwisie.

            def delete_chunks() -> None:
                with driver.session() as session:
                    session.execute_write(
                        lambda tx: tx.run(
                            "MATCH (n:RAGChunk {doc_id: $doc_id}) DETACH DELETE n",
                            doc_id=doc_id,
                        )
                    )

            await asyncio.to_thread(delete_chunks)
            logger.info("Usunięto wektorowe chunki dokumentu %s", doc_id)
        except Exception as exc:  # pragma: no cover - logujemy, ale nie przerywamy
            logger.error("Nie udało się usunąć chunków dokumentu %s z Neo4j: %s", doc_id, exc)

    def get_demographic_graph_context(
        self,
        age_group: str,
        location: str,
        education: str,
        gender: str
    ) -> List[Dict[str, Any]]:
        """Pobiera strukturalny kontekst z grafu wiedzy dla profilu demograficznego.

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

        # Mapowanie PL → EN dla dual-language search
        # Problem: Graph nodes mogą mieć właściwości w języku angielskim (legacy data)
        # Rozwiązanie: Dodajemy angielskie odpowiedniki polskich terminów
        PL_TO_EN_SEARCH_TERMS = {
            "wykształcenie wyższe": "higher education",
            "studia": "university",
            "uniwersytet": "university",
            "wykształcenie średnie": "secondary education",
            "liceum": "high school",
            "zasadnicze zawodowe": "vocational",
            "demografia": "demographic",
            "społeczeństwo polskie": "Polish society",
            "populacja": "population",
            "kobieta": "female",
            "mężczyzna": "male",
            "zatrudnienie": "employment",
            "praca": "work",
            "dochód": "income",
            "zarobki": "earnings",
            "mieszkanie": "housing",
            "edukacja": "education",
            "zdrowie": "health",
            "kultura": "culture",
            "wskaźnik": "indicator",
            "statystyka": "statistic",
            "dane": "data",
            "badanie": "research",
            "raport": "report",
            "analiza": "analysis",
        }

        # Budujemy search terms dla zapytania
        # Normalizuj wartości dla lepszego matchingu
        search_terms = []

        # Wiek - ekstrakcja liczb z zakresu
        if "-" in age_group:
            age_parts = age_group.split("-")
            search_terms.extend(age_parts)
        search_terms.append(age_group)

        # Lokalizacja
        search_terms.append(location)

        # Wykształcenie - normalizuj + dual-language
        if "wyższe" in education.lower():
            search_terms.extend(["wykształcenie wyższe", "studia", "uniwersytet"])
        elif "średnie" in education.lower():
            search_terms.extend(["wykształcenie średnie", "liceum"])
        elif "zawodowe" in education.lower():
            search_terms.extend(["zasadnicze zawodowe", "zawodowe"])
        else:
            search_terms.append(education)

        # Płeć
        search_terms.append(gender)

        # Dodaj ogólne terminy demograficzne (więcej aby zwiększyć szanse na match)
        search_terms.extend([
            "demografia", "społeczeństwo polskie", "populacja",
            "ludność", "mieszkańcy", "obywatele",
            "młodzi", "dorośli", "seniorzy",  # Generic age terms
            "wiek", "pokolenie", "generacja",
            "miasto", "miejski", "miejska",  # Generic location terms
            "polska", "polski", "polacy"  # Country terms
        ])

        # DUAL-LANGUAGE: Dodaj angielskie odpowiedniki dla polskich terminów
        # Tworzy kopię aby nie modyfikować listy podczas iteracji
        search_terms_copy = search_terms.copy()
        for pl_term in search_terms_copy:
            pl_normalized = pl_term.lower().strip()
            if pl_normalized in PL_TO_EN_SEARCH_TERMS:
                en_term = PL_TO_EN_SEARCH_TERMS[pl_normalized]
                if en_term not in search_terms:  # Unikaj duplikatów
                    search_terms.append(en_term)

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
            # Zapytanie Cypher: Znajdź węzły które pasują do search terms
            # pewnosc jest opcjonalny - preferujemy 'wysoka' ale akceptujemy wszystkie
            # UWAGA: Schema uproszczony - properties: streszczenie, skala, pewnosc, okres_czasu, kluczowe_fakty
            cypher_query = """
            // Parametry: $search_terms - lista słów kluczowych do matchingu
            // UWAGA: Schema używa POLSKICH property names (streszczenie, skala, pewnosc, etc.)

            // 1. Znajdź Wskaźniki (preferuj wysoką pewność jeśli istnieje)
            // Case-insensitive search
            MATCH (ind:Wskaznik)
            WHERE ANY(term IN $search_terms WHERE
                toLower(coalesce(ind.streszczenie, '')) CONTAINS toLower(term) OR
                toLower(coalesce(ind.kluczowe_fakty, '')) CONTAINS toLower(term)
            )
            WITH ind
            ORDER BY
                CASE WHEN ind.pewnosc = 'wysoka' THEN 0
                     WHEN ind.pewnosc = 'srednia' THEN 1
                     ELSE 2 END,
                size(coalesce(ind.kluczowe_fakty, '')) DESC
            LIMIT 3
            WITH collect({
                type: 'Wskaznik',
                streszczenie: ind.streszczenie,
                kluczowe_fakty: ind.kluczowe_fakty,
                skala: ind.skala,
                pewnosc: coalesce(ind.pewnosc, 'nieznana'),
                okres_czasu: ind.okres_czasu
            }) AS indicators

            // 2. Znajdź Obserwacje (preferuj wysoką pewność jeśli istnieje)
            // Case-insensitive search
            MATCH (obs:Obserwacja)
            WHERE ANY(term IN $search_terms WHERE
                toLower(coalesce(obs.streszczenie, '')) CONTAINS toLower(term) OR
                toLower(coalesce(obs.kluczowe_fakty, '')) CONTAINS toLower(term)
            )
            WITH indicators, obs
            ORDER BY
                CASE WHEN obs.pewnosc = 'wysoka' THEN 0
                     WHEN obs.pewnosc = 'srednia' THEN 1
                     ELSE 2 END,
                size(coalesce(obs.kluczowe_fakty, '')) DESC
            LIMIT 3
            WITH indicators, collect({
                type: 'Obserwacja',
                streszczenie: obs.streszczenie,
                kluczowe_fakty: obs.kluczowe_fakty,
                pewnosc: coalesce(obs.pewnosc, 'nieznana'),
                okres_czasu: obs.okres_czasu
            }) AS observations

            // 3. Znajdź Trendy
            // Case-insensitive search
            MATCH (trend:Trend)
            WHERE ANY(term IN $search_terms WHERE
                toLower(coalesce(trend.streszczenie, '')) CONTAINS toLower(term) OR
                toLower(coalesce(trend.kluczowe_fakty, '')) CONTAINS toLower(term)
            )
            WITH indicators, observations, trend
            ORDER BY size(coalesce(trend.kluczowe_fakty, '')) DESC
            LIMIT 2
            WITH indicators, observations, collect({
                type: 'Trend',
                streszczenie: trend.streszczenie,
                kluczowe_fakty: trend.kluczowe_fakty,
                okres_czasu: trend.okres_czasu
            }) AS trends

            // 4. Znajdź węzły Demografii
            // Case-insensitive search
            MATCH (demo:Demografia)
            WHERE ANY(term IN $search_terms WHERE
                toLower(coalesce(demo.streszczenie, '')) CONTAINS toLower(term) OR
                toLower(coalesce(demo.kluczowe_fakty, '')) CONTAINS toLower(term)
            )
            WITH indicators, observations, trends, demo
            ORDER BY
                CASE WHEN demo.pewnosc = 'wysoka' THEN 0
                     WHEN demo.pewnosc = 'srednia' THEN 1
                     ELSE 2 END
            LIMIT 2
            WITH indicators, observations, trends, collect({
                type: 'Demografia',
                streszczenie: demo.streszczenie,
                kluczowe_fakty: demo.kluczowe_fakty,
                pewnosc: coalesce(demo.pewnosc, 'nieznana')
            }) AS demographics

            // 5. Połącz wszystkie wyniki
            RETURN indicators + observations + trends + demographics AS graph_context
            """

            result = self.graph_store.query(
                cypher_query,
                params={"search_terms": search_terms}
            )

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

            return graph_context

        except Exception as exc:
            logger.error(
                "Błąd podczas pobierania graph context: %s",
                exc,
                exc_info=True
            )
            return []


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

            # Inicjalizuj RAGDocumentService dla dostępu do graph context
            # Używamy leniwej inicjalizacji aby uniknąć circular dependency
            self._rag_doc_service = None

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
            self._rag_doc_service = None
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
    def rag_doc_service(self) -> RAGDocumentService:
        """Leniwą inicjalizacja RAGDocumentService dla dostępu do graph context."""
        if self._rag_doc_service is None:
            self._rag_doc_service = RAGDocumentService()
        return self._rag_doc_service

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

    async def _keyword_search(self, query: str, k: int = 5) -> List[Document]:
        """Wykonuje wyszukiwanie pełnotekstowe w Neo4j i zwraca dokumenty LangChain."""

        if not self.vector_store:
            return []

        # Lazy initialization fulltext index przy pierwszym użyciu
        if settings.RAG_USE_HYBRID_SEARCH and not self._fulltext_index_initialized:
            await self._ensure_fulltext_index()
            self._fulltext_index_initialized = True

        try:
            driver = self.vector_store._driver

            def search() -> List[Document]:
                with driver.session() as session:
                    def run_query(tx):
                        result = tx.run(
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
                        documents: List[Document] = []
                        for record in result:
                            documents.append(
                                Document(
                                    page_content=record["text"],
                                    metadata={
                                        "doc_id": record["doc_id"],
                                        "title": record["title"],
                                        "chunk_index": record["chunk_index"],
                                        "keyword_score": record["score"],
                                    },
                                )
                            )
                        return documents

                    return session.execute_read(run_query)

            documents = await asyncio.to_thread(search)
            logger.info("Keyword search zwróciło %s wyników", len(documents))
            return documents
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
                graph_nodes = self.rag_doc_service.get_demographic_graph_context(
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
                "citations": citations,
                "query": query,
                "num_results": len(final_results),
                "search_type": search_type,
            }
        except Exception as exc:  # pragma: no cover - zwracamy pusty kontekst
            logger.error("Hybrydowe wyszukiwanie nie powiodło się: %s", exc, exc_info=True)
            return {"context": "", "citations": [], "query": query, "num_results": 0}

    def _rrf_fusion(
        self,
        vector_results: List[Tuple[Document, float]],
        keyword_results: List[Document],
        k: int = 60,
    ) -> List[Tuple[Document, float]]:
        """Łączy wyniki vector i keyword search przy pomocy Reciprocal Rank Fusion."""

        scores: Dict[int, float] = {}
        doc_map: Dict[int, Tuple[Document, float]] = {}

        for rank, (doc, original_score) in enumerate(vector_results):
            doc_hash = hash(doc.page_content)
            scores[doc_hash] = scores.get(doc_hash, 0.0) + 1.0 / (k + rank + 1)
            doc_map[doc_hash] = (doc, original_score)

        for rank, doc in enumerate(keyword_results):
            doc_hash = hash(doc.page_content)
            scores[doc_hash] = scores.get(doc_hash, 0.0) + 1.0 / (k + rank + 1)
            if doc_hash not in doc_map:
                doc_map[doc_hash] = (doc, 0.0)

        fused = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return [(doc_map[doc_hash][0], fused_score) for doc_hash, fused_score in fused]