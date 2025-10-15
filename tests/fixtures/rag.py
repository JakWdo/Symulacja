"""Fixtures dedicated to RAG / Graph analytics components."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_neo4j_driver():
    """Return an AsyncMock that mirrors the AsyncDriver contract."""
    driver = AsyncMock()
    session = AsyncMock()
    session.run = AsyncMock()
    session.execute_write = AsyncMock()
    session.execute_read = AsyncMock()

    driver.session = MagicMock(return_value=session)
    driver.close = AsyncMock()
    return driver


@pytest.fixture
def mock_vector_store():
    """Mock Neo4j vector store calls for hybrid search tests."""
    vector_store = AsyncMock()

    async def mock_similarity_search(query: str, k: int = 5):
        from langchain_core.documents import Document

        return [
            Document(
                page_content=f"Sample document {i} about {query}",
                metadata={
                    "doc_id": f"doc_{i}",
                    "title": f"Document {i}",
                    "chunk_index": i,
                },
            )
            for i in range(k)
        ]

    async def mock_similarity_search_with_score(query: str, k: int = 5):
        docs = await mock_similarity_search(query, k)
        return [(doc, 0.9 - (i * 0.1)) for i, doc in enumerate(docs)]

    vector_store.asimilarity_search = mock_similarity_search
    vector_store.asimilarity_search_with_score = mock_similarity_search_with_score
    vector_store.aadd_documents = AsyncMock()
    return vector_store


@pytest.fixture
def mock_graph_store():
    """Mock Neo4j graph store used by GraphRAG services."""
    graph_store = MagicMock()

    def mock_query(cypher: str, params: dict | None = None):
        return [
            {
                "type": "Indicator",
                "summary": "Employment rate 78.4%",
                "magnitude": "78.4%",
                "confidence": "high",
                "time_period": "2022",
                "source": "GUS",
            }
        ]

    graph_store.query.side_effect = mock_query
    return graph_store


@pytest.fixture
def mock_embeddings():
    """Return deterministic embeddings for vector search tests."""
    embeddings = MagicMock()

    def embed_query(text: str):
        np.random.seed(hash(text) % (2**32))
        return np.random.rand(768).tolist()

    def embed_documents(texts: list[str]):
        return [embed_query(text) for text in texts]

    embeddings.embed_query = embed_query
    embeddings.embed_documents = embed_documents
    return embeddings


@pytest.fixture
def mock_concept_extraction():
    """Mock asynchronous concept extraction used in graph analytics."""
    async def extract_concepts(text: str) -> dict[str, Any]:
        words = text.lower().split()
        concepts = [w.capitalize() for w in words if len(w) > 5][:5]

        return {
            "concepts": concepts or ["General", "Topic"],
            "emotions": ["Neutral"],
            "sentiment": 0.0,
            "key_phrases": [text[:50]] if text else [],
        }

    return AsyncMock(side_effect=extract_concepts)


@pytest.fixture
def mock_gemini_2_5_pro():
    """Return an AsyncMock that mimics the Gemini 2.5 Pro LLM."""
    llm = AsyncMock()
    allocation_plan = {
        "total_personas": 20,
        "overall_context": (
            "Polskie społeczeństwo w 2024 roku charakteryzuje się wysoką stopą zatrudnienia "
            "młodych dorosłych z wyższym wykształceniem (78.4%). "
        ),
        "groups": [
            {
                "count": 6,
                "demographics": {
                    "age": "25-34",
                    "gender": "kobieta",
                    "education": "wyższe",
                    "location": "Warszawa",
                },
                "brief": "Ta grupa stanowi około 17.3% populacji miejskiej według GUS 2022.",
                "graph_insights": [
                    {
                        "type": "Wskaznik",
                        "summary": "Stopa zatrudnienia kobiet 25-34 z wyższym",
                        "magnitude": "78.4%",
                        "confidence": "high",
                        "time_period": "2022",
                        "source": "GUS",
                        "why_matters": "Wysoka stopa zatrudnienia oznacza purchasing power",
                    }
                ],
                "allocation_reasoning": "6 z 20 person (30%) bo grupa kluczowa dla early adoption",
            }
        ],
    }

    llm.ainvoke.return_value = SimpleNamespace(
        content=f"```json\n{json.dumps(allocation_plan, ensure_ascii=False, indent=2)}\n```"
    )
    return llm


@pytest_asyncio.fixture
async def rag_document_service_with_mocks(mock_vector_store, mock_graph_store, mock_embeddings):
    """Instantiate RAGDocumentService with mocked dependencies to avoid network calls."""
    from app.services.rag_document_service import RAGDocumentService

    with patch("app.services.rag_document_service.GoogleGenerativeAIEmbeddings", return_value=mock_embeddings):
        service = RAGDocumentService()
        service.vector_store = mock_vector_store
        service.graph_store = mock_graph_store
        yield service


@pytest_asyncio.fixture
async def polish_society_rag_with_mocks(mock_vector_store, mock_embeddings):
    """Return a PolishSocietyRAG instance backed by fake vector store and embeddings."""
    from app.services.rag_hybrid_search_service import PolishSocietyRAG

    with patch("app.services.rag_hybrid_search_service.GoogleGenerativeAIEmbeddings", return_value=mock_embeddings):
        rag = PolishSocietyRAG()
        rag.vector_store = mock_vector_store
        rag._fulltext_index_initialized = True
        yield rag


@pytest_asyncio.fixture
async def graph_service_with_mocks(mock_neo4j_driver, mock_llm):
    """Return GraphService wired to mocked Neo4j driver and LLM."""
    from app.services.archived.graph_service import GraphService

    service = GraphService()
    service.driver = mock_neo4j_driver
    service.llm = mock_llm
    yield service


@pytest_asyncio.fixture
async def persona_orchestration_with_mocks(mock_gemini_2_5_pro, polish_society_rag_with_mocks):
    """Return PersonaOrchestrationService with mocked Gemini and RAG dependencies."""
    from app.services.persona_orchestration import PersonaOrchestrationService

    service = PersonaOrchestrationService()
    service.llm = mock_gemini_2_5_pro
    service.rag_service = await polish_society_rag_with_mocks
    yield service

