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
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain_experimental.graph_transformers.llm import LLMGraphTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings
from app.core.prompts.rag_prompts import (
    GRAPH_TRANSFORMER_ALLOWED_NODES,
    GRAPH_TRANSFORMER_ALLOWED_RELATIONSHIPS,
    GRAPH_TRANSFORMER_NODE_PROPERTIES,
    GRAPH_TRANSFORMER_RELATIONSHIP_PROPERTIES,
    GRAPH_TRANSFORMER_ADDITIONAL_INSTRUCTIONS,
)
from app.models.rag_document import RAGDocument
from app.services.shared.clients import build_chat_model
from app.services.rag.rag_clients import get_graph_store, get_vector_store

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

        from config import models

        self.settings = settings

        # Model config z centralnego registry
        model_config = models.get("rag", "graph")
        self.llm = build_chat_model(**model_config.params)

        # Połączenia do Neo4j (współdzielone, z retry logic)
        self.vector_store = get_vector_store(logger)
        self.graph_store = get_graph_store(logger)

    async def ingest_document(self, file_path: str, metadata: dict[str, Any]) -> dict[str, Any]:
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
                    logger.info(
                        "Generuję strukturę grafową na podstawie uniwersalnego modelu.",
                        extra={"doc_id": str(doc_id), "chunk_count": len(chunks)}
                    )
                    transformer = LLMGraphTransformer(
                        llm=self.llm,
                        allowed_nodes=GRAPH_TRANSFORMER_ALLOWED_NODES,
                        allowed_relationships=GRAPH_TRANSFORMER_ALLOWED_RELATIONSHIPS,
                        node_properties=GRAPH_TRANSFORMER_NODE_PROPERTIES,
                        relationship_properties=GRAPH_TRANSFORMER_RELATIONSHIP_PROPERTIES,
                        additional_instructions=GRAPH_TRANSFORMER_ADDITIONAL_INSTRUCTIONS,
                    )
                    graph_documents = await transformer.aconvert_to_graph_documents(chunks)

                    # Wzbogacenie węzłów o metadane dokumentu (współdzielona logika GraphRAGService)
                    from app.services.rag.rag_graph_service import GraphRAGService
                    enriched_graph_documents = GraphRAGService.enrich_graph_nodes(
                        graph_documents,
                        doc_id=str(doc_id),
                        metadata=metadata
                    )

                    self.graph_store.add_graph_documents(enriched_graph_documents, include_source=True)
                    logger.info(
                        "Zapisano strukturę grafową dla dokumentu %s",
                        doc_id,
                        extra={
                            "doc_id": str(doc_id),
                            "graph_nodes_count": len(enriched_graph_documents)
                        }
                    )
                except KeyError as key_exc:  # Specyficzny handling dla template errors
                    error_msg = str(key_exc)
                    logger.error(
                        "❌ Graph transformer template error for document %s: %s",
                        doc_id,
                        error_msg,
                        extra={
                            "doc_id": str(doc_id),
                            "error_type": "template_variable_error",
                            "error_stage": "graph_transformation",
                            "suggestion": "Check GRAPH_TRANSFORMER_ADDITIONAL_INSTRUCTIONS for unescaped curly braces",
                            "user_message": "Nie udało się wygenerować grafu wiedzy (błąd szablonu). Dokument zostanie zapisany bez struktury grafowej."
                        }
                    )
                    # Kontynuuj bez grafu - vector store zostanie zapisany normalnie
                except Exception as graph_exc:  # pragma: no cover - catch-all dla innych błędów
                    logger.error(
                        "❌ Nie udało się wygenerować grafu wiedzy dla dokumentu %s: %s",
                        doc_id,
                        str(graph_exc)[:200],  # Limit error message length
                        extra={
                            "doc_id": str(doc_id),
                            "error_type": type(graph_exc).__name__,
                            "error_stage": "graph_transformation",
                            "user_message": f"Nie udało się wygenerować grafu wiedzy ({type(graph_exc).__name__}). Dokument zostanie zapisany bez struktury grafowej."
                        },
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

    async def list_documents(self, db: AsyncSession) -> list[RAGDocument]:
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
