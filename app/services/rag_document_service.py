"""Serwis zarządzający dokumentami RAG - wczytywanie, chunking, vector store.

Ten moduł odpowiada za podstawową infrastrukturę przetwarzania dokumentów:
- Wczytywanie PDF/DOCX
- Dzielenie na chunki
- Generowanie embeddingów
- Zapis do Neo4j Vector Store
- Zarządzanie dokumentami (lista, usuwanie)

Graph RAG funkcjonalność znajduje się w rag_graph_service.py
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
from langchain_experimental.graph_transformers.llm import LLMGraphTransformer
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings
from app.models.rag_document import RAGDocument

settings = get_settings()
logger = logging.getLogger(__name__)


class RAGDocumentService:
    """Serwis zarządzający dokumentami, indeksem wektorowym.

    Zakres odpowiedzialności:

    1. Wczytywanie dokumentów PDF/DOCX i dzielenie ich na fragmenty.
    2. Generowanie embeddingów i zapis chunków w indeksie wektorowym Neo4j.
    3. Zarządzanie dokumentami w bazie PostgreSQL (lista, usuwanie z czyszczeniem
       danych w Neo4j).

    Uwaga: Budowa grafu wiedzy i Graph RAG znajdują się w GraphRAGService.
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

KRYTYCZNE OGRANICZENIA ILOŚCIOWE:
- MAX 3 WĘZŁY na chunk (tylko najważniejsze!)
- MAX 5 RELACJI na chunk
- Tylko pewnosc "wysoka" lub "srednia" (NIGDY "niska")
- Jeśli chunk nie zawiera WAŻNYCH informacji → 0 węzłów (to OK!)

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
- pewnosc (MUST): TYLKO "wysoka" lub "srednia" (NIGDY "niska")
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

=== DEDUPLIKACJA (KRYTYCZNE!) ===
Przed utworzeniem węzła sprawdź czy podobny już istnieje:
- "Stopa zatrudnienia kobiet 25-34" ≈ "Zatrudnienie młodych kobiet" → MERGE
- Używaj POWIAZANY_Z aby łączyć podobne koncepty zamiast tworzyć duplikaty
- Priorytet: 1 PRECYZYJNY węzeł > 3 podobne węzły

=== CONFIDENCE FILTERING (KRYTYCZNE!) ===
- TYLKO pewnosc "wysoka" lub "srednia"
- Jeśli informacja jest niepewna/nieweryfikowalna → NIE TWÓRZ węzła
- Priorytet: 1 PEWNY węzeł > 5 niepewnych węzłów

=== VALIDATION RULES ===
- streszczenie: Zawsze wypełnij (1 zdanie, max 150 znaków)
- pewnosc: Zawsze wypełnij (TYLKO "wysoka" lub "srednia" - jeśli niska → nie twórz węzła!)
- skala: Tylko dla Wskaznik (inne: opcjonalnie)
- kluczowe_fakty: Max 3 fakty, separated by semicolons
- doc_id, chunk_index: KRYTYCZNE dla lifecycle (zachowane automatycznie)

=== FOCUS ===
Priorytet: JAKOŚĆ > ilość. MAX 3 węzły, TYLKO pewne informacje. Mniej = lepiej.
                        """.strip(),
                    )
                    graph_documents = await transformer.aconvert_to_graph_documents(chunks)

                    # Wzbogacenie węzłów o metadane dokumentu
                    # Uwaga: _enrich_graph_nodes jest teraz w GraphRAGService
                    # Ale dla document ingest używamy lokalnej metody
                    from app.services.rag_graph_service import GraphRAGService
                    graph_service = GraphRAGService()
                    enriched_graph_documents = graph_service._enrich_graph_nodes(
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
