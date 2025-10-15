"""
Testy jednostkowe dla RAGDocumentService

Zakres testów:
- Document CRUD operations (list, delete)
- Neo4j connection retry logic
- Document status management

NIE testujemy:
- Ingest pipeline (complex, requires integration test)
- Graph building (delegowane do GraphRAGService)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.rag_document_service import RAGDocumentService


class TestRAGDocumentServiceInit:
    """Testy inicjalizacji serwisu"""

    def test_init_creates_embeddings(self):
        """Test: __init__ tworzy embeddings model"""
        with patch('app.services.rag_document_service.GoogleGenerativeAIEmbeddings') as mock_embeddings_class:
            service = RAGDocumentService()

            assert service.embeddings is not None
            mock_embeddings_class.assert_called_once()

    def test_init_creates_vector_store(self):
        """Test: __init__ tworzy vector store (z retry)"""
        with patch('app.services.rag_document_service.GoogleGenerativeAIEmbeddings'):
            with patch.object(RAGDocumentService, '_init_vector_store_with_retry') as mock_init_vector:
                mock_init_vector.return_value = MagicMock()

                service = RAGDocumentService()

                assert service.vector_store is not None
                mock_init_vector.assert_called_once()

    def test_init_creates_graph_store(self):
        """Test: __init__ tworzy graph store (z retry)"""
        with patch('app.services.rag_document_service.GoogleGenerativeAIEmbeddings'):
            with patch.object(RAGDocumentService, '_init_vector_store_with_retry', return_value=MagicMock()):
                with patch.object(RAGDocumentService, '_init_graph_store_with_retry') as mock_init_graph:
                    mock_init_graph.return_value = MagicMock()

                    service = RAGDocumentService()

                    assert service.graph_store is not None
                    mock_init_graph.assert_called_once()


class TestVectorStoreRetry:
    """Testy retry logic dla Neo4j Vector Store"""

    def test_vector_store_retry_success_first_attempt(self):
        """Test: Vector store połączenie udaje się za pierwszym razem"""
        with patch('app.services.rag_document_service.Neo4jVector') as mock_neo4j_vector:
            with patch('app.services.rag_document_service.GoogleGenerativeAIEmbeddings'):
                mock_neo4j_vector.from_existing_index.return_value = MagicMock()

                service = RAGDocumentService()

                assert service.vector_store is not None
                assert mock_neo4j_vector.from_existing_index.call_count == 1

    def test_vector_store_retry_success_after_failures(self):
        """Test: Vector store połączenie udaje się po kilku niepowodzeniach"""
        with patch('app.services.rag_document_service.Neo4jVector') as mock_neo4j_vector:
            with patch('app.services.rag_document_service.GoogleGenerativeAIEmbeddings'):
                with patch('app.services.rag_document_service.time.sleep'):  # Speed up test
                    # Fail 2 times, then succeed
                    mock_neo4j_vector.from_existing_index.side_effect = [
                        Exception("Connection refused"),
                        Exception("Connection refused"),
                        MagicMock()  # Success
                    ]

                    service = RAGDocumentService()

                    assert service.vector_store is not None
                    assert mock_neo4j_vector.from_existing_index.call_count == 3

    def test_vector_store_retry_max_retries_exceeded(self):
        """Test: Vector store raise exception po wyczerpaniu retry"""
        with patch('app.services.rag_document_service.Neo4jVector') as mock_neo4j_vector:
            with patch('app.services.rag_document_service.GoogleGenerativeAIEmbeddings'):
                with patch('app.services.rag_document_service.time.sleep'):
                    mock_neo4j_vector.from_existing_index.side_effect = Exception("Connection refused")

                    with pytest.raises(Exception, match="Connection refused"):
                        RAGDocumentService()


class TestGraphStoreRetry:
    """Testy retry logic dla Neo4j Graph Store"""

    def test_graph_store_retry_success_first_attempt(self):
        """Test: Graph store połączenie udaje się za pierwszym razem"""
        with patch('app.services.rag_document_service.Neo4jGraph') as mock_neo4j_graph:
            with patch('app.services.rag_document_service.GoogleGenerativeAIEmbeddings'):
                with patch.object(RAGDocumentService, '_init_vector_store_with_retry', return_value=MagicMock()):
                    mock_neo4j_graph.return_value = MagicMock()

                    service = RAGDocumentService()

                    assert service.graph_store is not None
                    assert mock_neo4j_graph.call_count == 1

    def test_graph_store_retry_success_after_failures(self):
        """Test: Graph store połączenie udaje się po kilku niepowodzeniach"""
        with patch('app.services.rag_document_service.Neo4jGraph') as mock_neo4j_graph:
            with patch('app.services.rag_document_service.GoogleGenerativeAIEmbeddings'):
                with patch.object(RAGDocumentService, '_init_vector_store_with_retry', return_value=MagicMock()):
                    with patch('app.services.rag_document_service.time.sleep'):
                        # Fail 2 times, then succeed
                        mock_neo4j_graph.side_effect = [
                            Exception("Connection refused"),
                            Exception("Connection refused"),
                            MagicMock()  # Success
                        ]

                        service = RAGDocumentService()

                        assert service.graph_store is not None
                        assert mock_neo4j_graph.call_count == 3


class TestListDocuments:
    """Testy listowania dokumentów"""

    async def test_list_documents_returns_all_active(self, rag_document_service_with_mocks):
        """Test: list_documents zwraca wszystkie aktywne dokumenty"""
        service = rag_document_service_with_mocks
        mock_db = AsyncMock()

        # Mock database query result
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = [
            MagicMock(id=uuid4(), title="Doc 1", status="completed"),
            MagicMock(id=uuid4(), title="Doc 2", status="completed"),
        ]
        mock_db.execute = AsyncMock(return_value=mock_result)

        documents = await service.list_documents(mock_db)

        assert len(documents) == 2
        assert documents[0].title == "Doc 1"
        assert documents[1].title == "Doc 2"

    async def test_list_documents_empty(self, rag_document_service_with_mocks):
        """Test: list_documents zwraca pustą listę gdy brak dokumentów"""
        service = rag_document_service_with_mocks
        mock_db = AsyncMock()

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        documents = await service.list_documents(mock_db)

        assert documents == []


class TestDeleteDocument:
    """Testy usuwania dokumentów"""

    async def test_delete_document_success(self, rag_document_service_with_mocks):
        """Test: delete_document usuwa dokument z DB i Neo4j"""
        service = rag_document_service_with_mocks
        mock_db = AsyncMock()
        doc_id = uuid4()

        # Mock database get
        mock_doc = MagicMock(id=doc_id, title="Test Doc", status="completed")
        mock_db.get = AsyncMock(return_value=mock_doc)
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        # Mock Neo4j cleanup
        service._delete_chunks_from_neo4j = AsyncMock()

        await service.delete_document(doc_id, mock_db)

        # Verify DB operations
        mock_db.delete.assert_called_once_with(mock_doc)
        mock_db.commit.assert_called_once()

        # Verify Neo4j cleanup
        service._delete_chunks_from_neo4j.assert_called_once_with(str(doc_id))

    async def test_delete_document_not_found(self, rag_document_service_with_mocks):
        """Test: delete_document raise ValueError gdy dokument nie istnieje"""
        service = rag_document_service_with_mocks
        mock_db = AsyncMock()
        doc_id = uuid4()

        # Mock document not found
        mock_db.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="not found"):
            await service.delete_document(doc_id, mock_db)


class TestDeleteChunksFromNeo4j:
    """Testy czyszczenia chunków z Neo4j"""

    async def test_delete_chunks_deletes_nodes_and_relationships(self, rag_document_service_with_mocks):
        """Test: _delete_chunks_from_neo4j usuwa nodes i relationships"""
        service = rag_document_service_with_mocks
        doc_id = str(uuid4())

        # Mock graph store query execution
        service.graph_store.query = MagicMock()

        await service._delete_chunks_from_neo4j(doc_id)

        # Verify graph store query was called (cleanup Cypher)
        assert service.graph_store.query.called

    async def test_delete_chunks_handles_neo4j_error(self, rag_document_service_with_mocks):
        """Test: _delete_chunks_from_neo4j loguje błąd Neo4j ale nie raise"""
        service = rag_document_service_with_mocks
        doc_id = str(uuid4())

        # Mock Neo4j error
        service.graph_store.query = MagicMock(side_effect=Exception("Neo4j error"))

        # Should not raise - errors are logged
        await service._delete_chunks_from_neo4j(doc_id)
