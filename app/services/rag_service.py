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
            model="gemini-1.5-pro",
            google_api_key=self.settings.GOOGLE_API_KEY,
            temperature=0,
        )

        # Embeddingi Google Gemini wykorzystywane przez indeks wektorowy Neo4j.
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
        )

        # Inicjalizacja Neo4j Vector Store – krytyczna dla działania RAG.
        try:
            self.vector_store = Neo4jVector(
                url=settings.NEO4J_URI,
                username=settings.NEO4J_USER,
                password=settings.NEO4J_PASSWORD,
                embedding=self.embeddings,
                index_name="rag_document_embeddings",
                node_label="RAGChunk",
                text_node_property="text",
                embedding_node_property="embedding",
            )
            logger.info("Neo4j Vector Store został poprawnie zainicjalizowany.")
        except Exception as exc:  # pragma: no cover - logujemy problem konfiguracyjny
            logger.error("Nie udało się zainicjalizować Neo4j Vector Store: %s", exc)
            self.vector_store = None

        # Inicjalizacja Neo4j Graph – może się nie udać, ale wtedy Graph RAG
        # zostanie tymczasowo wyłączony (pozostanie klasyczne RAG).
        try:
            self.graph_store = Neo4jGraph(
                url=settings.NEO4J_URI,
                username=settings.NEO4J_USER,
                password=settings.NEO4J_PASSWORD,
            )
            logger.info("Neo4j Graph Store został poprawnie zainicjalizowany.")
        except Exception as exc:  # pragma: no cover - logujemy problem konfiguracyjny
            logger.error("Nie udało się zainicjalizować Neo4j Graph Store: %s", exc)
            self.graph_store = None

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
                            "Observation",
                            "Indicator",
                            "Demographic",
                            "Trend",
                            "Location",
                            "Cause",
                            "Effect",
                        ],
                        allowed_relationships=[
                            "DESCRIBES",
                            "APPLIES_TO",
                            "SHOWS_TREND",
                            "LOCATED_IN",
                            "CAUSED_BY",
                            "LEADS_TO",
                            "COMPARES_TO",
                        ],
                        additional_instructions="""
                        Dla każdego fragmentu utwórz węzły opisujące obserwacje, wskaźniki
                        oraz zależności przyczynowo-skutkowe. Zachowaj metadane doc_id i
                        chunk_index w wygenerowanych węzłach, aby umożliwić późniejsze
                        usuwanie danych powiązanych z dokumentem.
                        """.strip(),
                    )
                    graph_documents = await transformer.aconvert_to_graph_documents(chunks)
                    self.graph_store.add_graph_documents(graph_documents, include_source=True)
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
                    Skup się na odnajdywaniu ścieżek do głębokości 3 pomiędzy kluczowymi encjami
                    (Observation, Indicator, Demographic, Trend, Location, Cause, Effect).
                    Zwracaj zapytania, które dostarczą pełnych właściwości węzłów oraz relacji.
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

        try:
            self.vector_store = Neo4jVector(
                url=settings.NEO4J_URI,
                username=settings.NEO4J_USER,
                password=settings.NEO4J_PASSWORD,
                embedding=self.embeddings,
                index_name="rag_document_embeddings",
                node_label="RAGChunk",
                text_node_property="text",
                embedding_node_property="embedding",
            )
            logger.info("PolishSocietyRAG został poprawnie zainicjalizowany.")

            if settings.RAG_USE_HYBRID_SEARCH:
                asyncio.create_task(self._ensure_fulltext_index())
        except Exception as exc:  # pragma: no cover - logujemy, ale nie przerywamy
            logger.error("Nie udało się zainicjalizować PolishSocietyRAG: %s", exc)
            self.vector_store = None

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

    async def get_demographic_insights(
        self,
        age_group: str,
        education: str,
        location: str,
        gender: str,
    ) -> Dict[str, Any]:
        """Buduje kontekst raportowy dla wskazanego profilu demograficznego."""

        if not self.vector_store:
            logger.warning("Vector store niedostępny – zwracam pusty kontekst.")
            return {"context": "", "citations": [], "query": "", "num_results": 0}

        query = (
            f"Profil demograficzny: {gender}, wiek {age_group}, wykształcenie {education}, "
            f"lokalizacja {location} w Polsce. Jakie są typowe cechy, wartości, zainteresowania, "
            f"style życia oraz aspiracje dla tej grupy?"
        )

        logger.info(
            "RAG hybrid search dla profilu: wiek=%s, edukacja=%s, lokalizacja=%s, płeć=%s",
            age_group,
            education,
            location,
            gender,
        )

        try:
            if settings.RAG_USE_HYBRID_SEARCH:
                vector_results = await self.vector_store.asimilarity_search_with_score(
                    query,
                    k=settings.RAG_TOP_K * 2,
                )
                keyword_results = await self._keyword_search(
                    query,
                    k=settings.RAG_TOP_K * 2,
                )
                fused_results = self._rrf_fusion(
                    vector_results,
                    keyword_results,
                    k=settings.RAG_RRF_K,
                )
                final_results = fused_results[: settings.RAG_TOP_K]
                search_type = "hybrid"
            else:
                final_results = await self.vector_store.asimilarity_search_with_score(
                    query,
                    k=settings.RAG_TOP_K,
                )
                search_type = "vector_only"

            context_chunks: List[str] = []
            citations: List[Dict[str, Any]] = []
            for doc, score in final_results:
                chunk_text = doc.page_content[:800] if len(doc.page_content) > 800 else doc.page_content
                context_chunks.append(chunk_text)
                citations.append(
                    {
                        "text": chunk_text,
                        "score": float(score),
                        "metadata": doc.metadata,
                    }
                )

            context = "\n\n---\n\n".join(context_chunks)
            if len(context) > settings.RAG_MAX_CONTEXT_CHARS:
                context = context[: settings.RAG_MAX_CONTEXT_CHARS] + "\n\n[... kontekst obcięty]"

            return {
                "context": context,
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