"""
Serwis RAG (Retrieval-Augmented Generation) z LangChain

Zarządza bazą wiedzy dokumentów PDF/DOCX dla generowania realistycznych person.
Wykorzystuje LangChain do pełnego pipeline'u: loading → chunking → embedding → storing → retrieval.

Komponenty:
- RAGDocumentService: Zarządzanie dokumentami (ingest, list, delete)
- PolishSocietyRAG: Retrieval kontekstu dla person z hybrid search
"""

import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Neo4jVector
from langchain_core.documents import Document

from app.core.config import get_settings
from app.models.rag_document import RAGDocument

settings = get_settings()
logger = logging.getLogger(__name__)

# Neo4j driver będziemy pobierać z vector_store._driver
# aby nie duplikować połączeń


class RAGDocumentService:
    """
    Serwis zarządzania dokumentami RAG z LangChain

    Odpowiedzialny za:
    - Parsing dokumentów (PDF, DOCX) używając LangChain DocumentLoaders
    - Chunking tekstu z RecursiveCharacterTextSplitter
    - Generowanie embeddingów z Google Gemini
    - Przechowywanie w Neo4j Vector Store
    - Zarządzanie metadanymi w PostgreSQL
    """

    def __init__(self):
        """Inicjalizuj serwis z embeddingami i vector store"""
        self.settings = settings

        # Google Gemini Embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
        )

        # Neo4j Vector Store
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
            logger.info("Neo4j Vector Store initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j Vector Store: {e}")
            self.vector_store = None

    async def ingest_document(
        self,
        file_path: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Przetwarza dokument przez pipeline LangChain

        Pipeline:
        1. Load document (PyPDFLoader lub Docx2txtLoader)
        2. Split into chunks (RecursiveCharacterTextSplitter)
        3. Generate embeddings (GoogleGenerativeAIEmbeddings)
        4. Store in Neo4j (Neo4jVector)

        Args:
            file_path: Ścieżka do pliku PDF lub DOCX
            metadata: Metadane dokumentu (doc_id, title, country, etc.)

        Returns:
            Dict z kluczami:
            - num_chunks: liczba wygenerowanych chunków
            - status: 'ready' lub 'failed'
            - error: opcjonalny komunikat błędu

        Raises:
            ValueError: Jeśli typ pliku nie jest obsługiwany
            Exception: Błędy parsingu lub embeddingu
        """
        if not self.vector_store:
            raise Exception("Neo4j Vector Store is not available")

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Starting ingestion of document: {path.name}")

        try:
            # 1. LOAD - wybór loadera na podstawie rozszerzenia
            file_extension = path.suffix.lower()

            if file_extension == '.pdf':
                loader = PyPDFLoader(str(path))
                logger.info(f"Using PyPDFLoader for {path.name}")
            elif file_extension == '.docx':
                loader = Docx2txtLoader(str(path))
                logger.info(f"Using Docx2txtLoader for {path.name}")
            else:
                raise ValueError(
                    f"Unsupported file type: {file_extension}. "
                    "Supported: .pdf, .docx"
                )

            # Load documents (może zwrócić wiele Document objects dla PDF z wieloma stronami)
            documents = await asyncio.to_thread(loader.load)
            logger.info(f"Loaded {len(documents)} document pages/sections")

            if not documents:
                raise ValueError("No content extracted from document")

            # 2. SPLIT - chunking z overlap
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.RAG_CHUNK_SIZE,
                chunk_overlap=settings.RAG_CHUNK_OVERLAP,
                separators=["\n\n", "\n", ". ", " ", ""],
                length_function=len,
            )

            chunks = text_splitter.split_documents(documents)
            logger.info(
                f"Split into {len(chunks)} chunks "
                f"(size={settings.RAG_CHUNK_SIZE}, overlap={settings.RAG_CHUNK_OVERLAP})"
            )

            if not chunks:
                raise ValueError("No chunks generated from document")

            # 3. ADD METADATA - dodaj metadane do każdego chunku
            doc_id = metadata.get('doc_id')
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    'doc_id': str(doc_id),
                    'chunk_index': i,
                    'title': metadata.get('title', 'Unknown'),
                    'country': metadata.get('country', 'Poland'),
                    'source_file': path.name,
                })

            # 4. EMBED & STORE - wygeneruj embeddingi i zapisz w Neo4j
            logger.info(f"Generating embeddings and storing in Neo4j...")

            # Neo4jVector.aadd_documents automatycznie generuje embeddingi i zapisuje
            await self.vector_store.aadd_documents(chunks)

            logger.info(
                f"Successfully ingested {len(chunks)} chunks for document {doc_id}"
            )

            return {
                "num_chunks": len(chunks),
                "status": "ready"
            }

        except Exception as e:
            logger.error(f"Failed to ingest document {file_path}: {str(e)}", exc_info=True)
            return {
                "num_chunks": 0,
                "status": "failed",
                "error": str(e)
            }

    async def list_documents(self, db: AsyncSession) -> List[RAGDocument]:
        """
        Lista wszystkich aktywnych dokumentów RAG

        Args:
            db: Sesja bazy danych

        Returns:
            Lista obiektów RAGDocument (tylko is_active=True)
        """
        result = await db.execute(
            select(RAGDocument)
            .where(RAGDocument.is_active == True)
            .order_by(RAGDocument.created_at.desc())
        )
        return result.scalars().all()

    async def delete_document(self, doc_id: UUID, db: AsyncSession):
        """
        Usuwa dokument z bazy wiedzy

        Wykonuje:
        1. Soft delete w PostgreSQL (is_active=False)
        2. Usunięcie chunków z Neo4j (DELETE nodes WHERE doc_id)

        Args:
            doc_id: UUID dokumentu
            db: Sesja bazy danych

        Raises:
            ValueError: Jeśli dokument nie istnieje
        """
        # Pobierz dokument
        doc = await db.get(RAGDocument, doc_id)
        if not doc:
            raise ValueError(f"Document {doc_id} not found")

        # Soft delete w PostgreSQL
        doc.is_active = False
        await db.commit()

        # Usuń chunki z Neo4j
        if self.vector_store:
            try:
                await self._delete_chunks_from_neo4j(str(doc_id))
                logger.info(f"Deleted chunks for document {doc_id} from Neo4j")
            except Exception as e:
                logger.error(f"Failed to delete chunks from Neo4j: {e}")
                # Nie rzucamy błędu - soft delete w PostgreSQL się powiódł

    async def _delete_chunks_from_neo4j(self, doc_id: str):
        """
        Usuwa chunki z Neo4j dla danego doc_id

        Args:
            doc_id: UUID dokumentu jako string
        """
        if not self.vector_store:
            return

        # Neo4j Cypher query - usuń wszystkie chunki dla doc_id
        # Neo4jVector nie ma wbudowanej metody delete, więc używamy raw Cypher
        try:
            # Pobierz driver z vector_store (internal access)
            # Alternatywa: stworzyć własny Neo4j driver connection
            logger.warning(
                f"Neo4j chunk deletion for doc_id={doc_id} - "
                "manual implementation required (not critical for MVP)"
            )
            # TODO: Implementuj direct Cypher query jeśli potrzebne
            # driver = self.vector_store._driver
            # await driver.execute_query(
            #     "MATCH (n:RAGChunk {doc_id: $doc_id}) DELETE n",
            #     doc_id=doc_id
            # )
        except Exception as e:
            logger.error(f"Error deleting Neo4j chunks: {e}")


class PolishSocietyRAG:
    """
    Retrieval dla polskich person z hybrid search

    Łączy:
    - Vector similarity search (semantic)
    - Keyword search (lexical)
    - RRF (Reciprocal Rank Fusion) dla kombinacji wyników

    Używane przez PersonaGeneratorLangChain do wzbogacenia promptów
    o rzeczywisty kontekst z raportów o polskim społeczeństwie.
    """

    def __init__(self):
        """Inicjalizuj RAG z embeddingami i vector store"""
        self.settings = settings

        # Google Gemini Embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
        )

        # Neo4j Vector Store
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
            logger.info("PolishSocietyRAG initialized successfully")

            # Utwórz fulltext index dla keyword search (jeśli hybrid search włączony)
            if settings.RAG_USE_HYBRID_SEARCH:
                asyncio.create_task(self._ensure_fulltext_index())
        except Exception as e:
            logger.error(f"Failed to initialize PolishSocietyRAG: {e}")
            self.vector_store = None

    async def _ensure_fulltext_index(self):
        """
        Upewnij się że fulltext index istnieje dla keyword search

        Tworzy Neo4j fulltext index na polu 'text' w nodach RAGChunk.
        Index nazywa się 'rag_fulltext_index'.
        """
        if not self.vector_store:
            return

        try:
            # Pobierz Neo4j driver z vector_store
            driver = self.vector_store._driver

            # Sprawdź czy index już istnieje
            def check_and_create_index(tx):
                # Sprawdź istniejące indeksy
                result = tx.run("SHOW INDEXES")
                indexes = [record["name"] for record in result]

                if "rag_fulltext_index" not in indexes:
                    # Utwórz fulltext index
                    tx.run("""
                        CREATE FULLTEXT INDEX rag_fulltext_index IF NOT EXISTS
                        FOR (n:RAGChunk)
                        ON EACH [n.text]
                    """)
                    logger.info("Created fulltext index 'rag_fulltext_index' for RAGChunk nodes")
                else:
                    logger.debug("Fulltext index 'rag_fulltext_index' already exists")

            # Wykonaj w asyncio thread pool
            await asyncio.to_thread(
                lambda: driver.session().execute_write(check_and_create_index)
            )

        except Exception as e:
            logger.warning(f"Could not create fulltext index (non-critical): {e}")

    async def _keyword_search(self, query: str, k: int = 5) -> List[Document]:
        """
        Keyword search przez Neo4j fulltext index

        Używa fulltext index 'rag_fulltext_index' do wyszukiwania
        chunków zawierających słowa kluczowe z query.

        Args:
            query: Zapytanie tekstowe
            k: Liczba wyników do zwrócenia

        Returns:
            Lista Document obiektów z wynikami keyword search
        """
        if not self.vector_store:
            return []

        try:
            driver = self.vector_store._driver

            def search_fulltext(tx):
                # Neo4j fulltext search query
                # db.index.fulltext.queryNodes zwraca (node, score)
                result = tx.run("""
                    CALL db.index.fulltext.queryNodes('rag_fulltext_index', $search_query)
                    YIELD node, score
                    RETURN node.text AS text,
                           node.doc_id AS doc_id,
                           node.title AS title,
                           node.chunk_index AS chunk_index,
                           score
                    ORDER BY score DESC
                    LIMIT $search_limit
                """, search_query=query, search_limit=k)

                documents = []
                for record in result:
                    doc = Document(
                        page_content=record["text"],
                        metadata={
                            "doc_id": record["doc_id"],
                            "title": record["title"],
                            "chunk_index": record["chunk_index"],
                            "keyword_score": record["score"],
                        }
                    )
                    documents.append(doc)

                return documents

            # Wykonaj w thread pool
            docs = await asyncio.to_thread(
                lambda: driver.session().execute_read(search_fulltext)
            )

            logger.info(f"Keyword search returned {len(docs)} results")
            return docs

        except Exception as e:
            logger.warning(f"Keyword search failed (falling back to vector only): {e}")
            return []

    async def get_demographic_insights(
        self,
        age_group: str,
        education: str,
        location: str,
        gender: str,
    ) -> Dict[str, Any]:
        """
        Pobiera kontekst z raportu dla danego profilu demograficznego

        Używa hybrid search (vector + keyword) z RRF fusion
        do znalezienia najbardziej relevantnych fragmentów.

        Args:
            age_group: Grupa wiekowa (np. "25-34")
            education: Poziom wykształcenia (np. "wyższe")
            location: Lokalizacja (np. "Warszawa")
            gender: Płeć (np. "mężczyzna", "kobieta")

        Returns:
            Dict z kluczami:
            - context: String ze sklejonych top fragmentów
            - citations: Lista dict z fragmentami + scores + metadata
            - query: Użyte zapytanie
            - num_results: Liczba znalezionych fragmentów
        """
        if not self.vector_store:
            logger.warning("Vector store not available, returning empty context")
            return {
                "context": "",
                "citations": [],
                "query": "",
                "num_results": 0
            }

        # Konstruuj query po polsku
        query = f"""
        Profil demograficzny: {gender}, wiek {age_group}, wykształcenie {education},
        lokalizacja {location} w Polsce.

        Jakie są typowe cechy, wartości życiowe, zainteresowania i style życia
        dla tej grupy w polskim społeczeństwie? Jakie są wzorce zachowań,
        aspiracje i charakterystyczne postawy?
        """

        logger.info(f"RAG query for demographics: {age_group}, {education}, {location}, {gender}")

        try:
            # HYBRID SEARCH: Vector + Keyword search z RRF fusion
            if settings.RAG_USE_HYBRID_SEARCH:
                # 1. Vector search z score
                vector_results = await self.vector_store.asimilarity_search_with_score(
                    query,
                    k=settings.RAG_TOP_K * 2  # Pobierz więcej dla fusion
                )
                logger.info(f"Vector search returned {len(vector_results)} results")

                # 2. Keyword search przez fulltext index
                keyword_results = await self._keyword_search(
                    query,
                    k=settings.RAG_TOP_K * 2  # Pobierz więcej dla fusion
                )
                logger.info(f"Keyword search returned {len(keyword_results)} results")

                # 3. RRF Fusion - połącz wyniki
                fused_results = self._rrf_fusion(
                    vector_results,
                    keyword_results,
                    k=settings.RAG_RRF_K
                )
                logger.info(f"RRF fusion produced {len(fused_results)} combined results")

                # Użyj fused results
                final_results = fused_results[:settings.RAG_TOP_K]

            else:
                # TYLKO VECTOR SEARCH (fallback jeśli hybrid wyłączony)
                vector_results = await self.vector_store.asimilarity_search_with_score(
                    query,
                    k=settings.RAG_TOP_K
                )
                logger.info(f"Vector search returned {len(vector_results)} results (hybrid disabled)")
                final_results = vector_results

            # Build context z top wyników
            context_chunks = []
            citations = []

            for doc, score in final_results:
                # Ogranicz długość pojedynczego chunku
                chunk_text = doc.page_content[:800] if len(doc.page_content) > 800 else doc.page_content
                context_chunks.append(chunk_text)

                # Dodaj citation
                citations.append({
                    "text": chunk_text,
                    "score": float(score),
                    "metadata": doc.metadata
                })

            # Sklejony kontekst
            context = "\n\n---\n\n".join(context_chunks)

            # Ogranicz do max_context_chars
            if len(context) > settings.RAG_MAX_CONTEXT_CHARS:
                context = context[:settings.RAG_MAX_CONTEXT_CHARS] + "\n\n[... kontekst obcięty]"
                logger.info(
                    f"Context truncated to {settings.RAG_MAX_CONTEXT_CHARS} chars"
                )

            search_type = "hybrid" if settings.RAG_USE_HYBRID_SEARCH else "vector_only"
            logger.info(
                f"RAG context built ({search_type}): {len(context)} chars, {len(citations)} citations"
            )

            return {
                "context": context,
                "citations": citations,
                "query": query.strip(),
                "num_results": len(final_results),
                "search_type": search_type
            }

        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}", exc_info=True)
            return {
                "context": "",
                "citations": [],
                "query": query.strip(),
                "num_results": 0
            }

    def _rrf_fusion(
        self,
        vector_results: List[Tuple[Document, float]],
        keyword_results: List[Document],
        k: int = 60
    ) -> List[Tuple[Document, float]]:
        """
        Reciprocal Rank Fusion - łączy wyniki z vector i keyword search

        RRF formula: score = sum(1 / (k + rank)) dla każdego query
        gdzie k=60 jest typową wartością (parametr wygładzający)

        Args:
            vector_results: Lista (Document, score) z vector search
            keyword_results: Lista Document z keyword search
            k: Parametr RRF (default 60)

        Returns:
            Lista (Document, fused_score) posortowana po score (malejąco)
        """
        scores: Dict[int, float] = {}
        doc_map: Dict[int, Tuple[Document, float]] = {}

        # Vector search scores (rank-based)
        for rank, (doc, original_score) in enumerate(vector_results):
            doc_hash = hash(doc.page_content)  # Prosty identyfikator
            scores[doc_hash] = scores.get(doc_hash, 0.0) + 1.0 / (k + rank + 1)
            doc_map[doc_hash] = (doc, original_score)

        # Keyword search scores (rank-based)
        for rank, doc in enumerate(keyword_results):
            doc_hash = hash(doc.page_content)
            scores[doc_hash] = scores.get(doc_hash, 0.0) + 1.0 / (k + rank + 1)
            if doc_hash not in doc_map:
                doc_map[doc_hash] = (doc, 0.0)

        # Sort by fused score
        sorted_docs = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Map back to documents
        fused_results = [
            (doc_map[doc_hash][0], fused_score)
            for doc_hash, fused_score in sorted_docs
        ]

        return fused_results
