"""
Pytest configuration and shared fixtures.

Ten plik zawiera fixtures używane przez wiele testów.
"""

import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.db.base import Base
from app.core.config import get_settings


# Konfiguracja event loop dla pytest-asyncio
@pytest.fixture(scope="session")
def event_loop():
    """
    Tworzy event loop dla całej sesji testowej.

    Zapobiega warnings o zamkniętym event loop.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# DATABASE FIXTURES (dla testów integracyjnych)
# ============================================================================

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """
    Tworzy engine testowej bazy danych.

    UWAGA: Wymaga uruchomionej bazy PostgreSQL.
    Użyj: docker-compose -f docker-compose.test.yml up -d
    """
    settings = get_settings()

    # Zamień nazwę bazy na testową
    test_db_url = settings.DATABASE_URL.replace(
        "/market_research_db",
        "/test_market_research_db"
    )

    engine = create_async_engine(
        test_db_url,
        echo=False,
        poolclass=NullPool,  # Disable pooling for tests
    )

    # Utwórz wszystkie tabele
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Tworzy sesję bazodanową dla pojedynczego testu.

    Po każdym teście wykonuje rollback, aby zapewnić izolację.

    Usage:
        @pytest.mark.asyncio
        async def test_something(db_session):
            # Use db_session like normal AsyncSession
            result = await db_session.execute(select(Model))
    """
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()


# ============================================================================
# MOCK FIXTURES (dla testów jednostkowych bez DB)
# ============================================================================

@pytest.fixture
def mock_settings():
    """
    Mock settings dla testów jednostkowych.

    Usage:
        def test_something(mock_settings):
            assert mock_settings.ENVIRONMENT == "test"
    """
    from unittest.mock import MagicMock

    settings = MagicMock()
    settings.ENVIRONMENT = "test"
    settings.DEBUG = True
    settings.GOOGLE_API_KEY = "test_api_key"
    settings.DEFAULT_MODEL = "gemini-2.5-flash"
    settings.TEMPERATURE = 0.7
    settings.MAX_TOKENS = 2048
    settings.RANDOM_SEED = 42

    return settings


@pytest.fixture
def mock_llm():
    """
    Mock LLM dla testów bez wywoływania prawdziwego Gemini API.

    Usage:
        async def test_something(mock_llm):
            response = await mock_llm.ainvoke("prompt")
            assert "test" in response.content
    """
    from unittest.mock import AsyncMock
    from types import SimpleNamespace

    llm = AsyncMock()
    llm.ainvoke.return_value = SimpleNamespace(
        content="This is a mocked LLM response for testing."
    )

    return llm


@pytest.fixture
def sample_persona_dict():
    """
    Przykładowy słownik danych persony dla testów.

    Usage:
        def test_persona_creation(sample_persona_dict):
            persona = Persona(**sample_persona_dict)
            assert persona.age == 30
    """
    from uuid import uuid4

    return {
        "id": uuid4(),
        "project_id": uuid4(),
        "age": 30,
        "gender": "female",
        "location": "Warsaw",
        "education_level": "Master",
        "income_bracket": "50k-70k",
        "occupation": "Software Engineer",
        "full_name": "Anna Kowalska",
        "background_story": "A creative professional who loves technology.",
        "values": ["Innovation", "Quality"],
        "openness": 0.8,
        "conscientiousness": 0.7,
        "extraversion": 0.6,
        "agreeableness": 0.7,
        "neuroticism": 0.3,
    }


@pytest.fixture
def sample_project_dict():
    """
    Przykładowy słownik projektu dla testów.
    """
    from uuid import uuid4

    return {
        "id": uuid4(),
        "owner_id": uuid4(),
        "name": "Test Research Project",
        "description": "Testing market research features",
        "target_demographics": {
            "age_group": {"25-34": 0.5, "35-44": 0.5},
            "gender": {"male": 0.5, "female": 0.5}
        },
        "target_sample_size": 20,
    }


# ============================================================================
# API FIXTURES (dla testów API)
# ============================================================================

@pytest.fixture
def api_client():
    """
    FastAPI TestClient dla testów API.

    Usage:
        def test_endpoint(api_client):
            response = api_client.get("/api/v1/projects")
            assert response.status_code == 200
    """
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def auth_headers():
    """
    Headers z tokenem autoryzacyjnym dla testów API.

    Usage:
        def test_protected_endpoint(api_client, auth_headers):
            response = api_client.get("/api/v1/projects", headers=auth_headers)
    """
    from app.core.security import create_access_token
    from uuid import uuid4

    token = create_access_token({"sub": str(uuid4())})
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """
    Konfiguracja pytest - dodaje custom markers.
    """
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (requires DB)"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests (requires full environment)"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running (>1s)"
    )


def pytest_collection_modifyitems(config, items):
    """
    Automatycznie dodaje markers do testów.
    """
    for item in items:
        # Oznacz testy asyncio
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)

        # Oznacz testy z db_session jako integration
        if "db_session" in item.fixturenames:
            item.add_marker(pytest.mark.integration)


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def temp_file(tmp_path):
    """
    Tworzy tymczasowy plik dla testów.

    Usage:
        def test_file_processing(temp_file):
            temp_file.write_text("test content")
            result = process_file(temp_file)
    """
    file_path = tmp_path / "test_file.txt"
    yield file_path
    # Cleanup automatic (tmp_path is cleaned by pytest)


@pytest.fixture
def mock_datetime():
    """
    Mock datetime dla deterministycznych testów.

    Usage:
        def test_timestamp(mock_datetime):
            from datetime import datetime
            with mock_datetime("2025-01-10 12:00:00"):
                assert datetime.now().hour == 12
    """
    from unittest.mock import patch
    from datetime import datetime

    class DatetimeMock:
        def __init__(self):
            self.fixed_time = None

        def __call__(self, time_str):
            self.fixed_time = datetime.fromisoformat(time_str)
            return patch('datetime.datetime', **{'now.return_value': self.fixed_time})

    return DatetimeMock()


# ============================================================================
# ADVANCED INTEGRATION FIXTURES
# ============================================================================

@pytest_asyncio.fixture
async def authenticated_client(db_session):
    """
    Zwraca TestClient + authenticated user + auth headers.

    Usage:
        async def test_something(authenticated_client):
            client, user, headers = authenticated_client
            response = client.get("/api/v1/projects", headers=headers)
            assert response.status_code == 200
    """
    from fastapi.testclient import TestClient
    from app.main import app
    from app.models.user import User
    from app.core.security import get_password_hash, create_access_token
    from uuid import uuid4

    # Create test user in database
    test_user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password=get_password_hash("SecurePass123"),
        full_name="Test User",
        is_active=True,
    )

    db_session.add(test_user)
    await db_session.commit()
    await db_session.refresh(test_user)

    # Create auth token
    token = create_access_token({"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # Create test client
    client = TestClient(app, raise_server_exceptions=False)

    return client, test_user, headers


@pytest_asyncio.fixture
async def project_with_personas(db_session, authenticated_client):
    """
    Zwraca project z 10 wygenerowanymi personami.

    Usage:
        async def test_focus_group(project_with_personas):
            project, personas, client, headers = project_with_personas
            # project ma 10 person gotowych do użycia
    """
    from app.models.project import Project
    from app.models.persona import Persona
    from uuid import uuid4

    client, user, headers = await authenticated_client

    # Create project
    project = Project(
        id=uuid4(),
        owner_id=user.id,
        name="Test Project with Personas",
        description="Project for testing",
        target_demographics={
            "age_group": {"18-24": 0.3, "25-34": 0.4, "35-44": 0.3},
            "gender": {"male": 0.5, "female": 0.5}
        },
        target_sample_size=10,
    )

    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create 10 test personas
    personas = []
    for i in range(10):
        persona = Persona(
            id=uuid4(),
            project_id=project.id,
            age=25 + (i * 3),  # Ages from 25 to 52
            gender="male" if i % 2 == 0 else "female",
            full_name=f"Test Persona {i+1}",
            location="Warsaw" if i < 5 else "Krakow",
            education_level="bachelors" if i < 7 else "masters",
            income_bracket="30k-60k" if i < 5 else "60k-100k",
            occupation=f"Professional {i+1}",
            background_story=f"Persona {i+1} is a professional interested in innovation.",
            values=["Quality", "Innovation"],
            interests=["Technology", "Business"],
            openness=0.7 + (i * 0.02),
            conscientiousness=0.6 + (i * 0.02),
            extraversion=0.5 + (i * 0.02),
            agreeableness=0.65 + (i * 0.02),
            neuroticism=0.4 - (i * 0.01),
        )
        personas.append(persona)
        db_session.add(persona)

    await db_session.commit()

    # Refresh all personas
    for persona in personas:
        await db_session.refresh(persona)

    return project, personas, client, headers


@pytest_asyncio.fixture
async def completed_focus_group(db_session, project_with_personas):
    """
    Zwraca completed focus group z responses.

    Usage:
        async def test_results(completed_focus_group):
            focus_group, responses, client, headers = completed_focus_group
            # focus_group.status == "completed"
            # responses = 15 (5 personas × 3 questions)
    """
    from app.models.focus_group import FocusGroup
    from app.models.persona_response import PersonaResponse
    from uuid import uuid4
    from datetime import datetime, timezone, timedelta

    project, personas, client, headers = await project_with_personas

    # Select 5 personas for focus group
    selected_personas = personas[:5]
    persona_ids = [str(p.id) for p in selected_personas]

    # Create focus group
    questions = [
        "What do you think about this product?",
        "Would you recommend it to friends?",
        "What improvements would you suggest?"
    ]

    focus_group = FocusGroup(
        id=uuid4(),
        project_id=project.id,
        name="Test Focus Group",
        description="Completed focus group for testing",
        persona_ids=persona_ids,
        questions=questions,
        mode="normal",
        status="completed",
        started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        completed_at=datetime.now(timezone.utc),
        total_execution_time_ms=120000,  # 2 minutes
        avg_response_time_ms=2400.0,     # 2.4s per response
    )

    db_session.add(focus_group)
    await db_session.commit()
    await db_session.refresh(focus_group)

    # Create responses (5 personas × 3 questions = 15 responses)
    responses = []
    response_texts = [
        "I think this is a great product with innovative features.",
        "Yes, I would definitely recommend it to my colleagues.",
        "I would suggest adding more customization options.",
        "The product looks promising but needs better documentation.",
        "I'm not sure yet, need to see more features.",
    ]

    for question_idx, question in enumerate(questions):
        for persona_idx, persona in enumerate(selected_personas):
            response = PersonaResponse(
                id=uuid4(),
                focus_group_id=focus_group.id,
                persona_id=persona.id,
                question_text=question,
                response_text=response_texts[persona_idx % len(response_texts)],
                response_time_ms=2000 + (persona_idx * 200),
            )
            responses.append(response)
            db_session.add(response)

    await db_session.commit()

    # Refresh all responses
    for response in responses:
        await db_session.refresh(response)

    return focus_group, responses, client, headers


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Resetuje singletony między testami.

    Zapobiega side effects między testami.
    """
    yield

    # Reset settings cache
    from app.core.config import get_settings
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def clear_graph_cache():
    """
    Czyści cache grafu między testami.
    """
    yield

    from app.services.graph_service import GraphService
    GraphService._memory_graph_cache = {}
    GraphService._memory_stats_cache = {}
    GraphService._memory_metrics_cache = {}


# ============================================================================
# RAG & GRAPHRAG FIXTURES (dla testów RAG/GraphRAG/Orchestration)
# ============================================================================

@pytest.fixture
def mock_neo4j_driver():
    """
    Mock Neo4j driver dla testów bez prawdziwego Neo4j.

    Usage:
        def test_graph_query(mock_neo4j_driver):
            # mock_neo4j_driver ma all standard methods
            session = mock_neo4j_driver.session()
    """
    from unittest.mock import AsyncMock, MagicMock

    driver = AsyncMock()
    session = AsyncMock()

    # Mock session methods
    session.run = AsyncMock()
    session.execute_write = AsyncMock()
    session.execute_read = AsyncMock()

    # Mock driver methods
    driver.session = MagicMock(return_value=session)
    driver.close = AsyncMock()

    return driver


@pytest.fixture
def mock_vector_store():
    """
    Mock Neo4jVector store dla testów hybrid search bez Neo4j.

    Usage:
        async def test_hybrid_search(mock_vector_store):
            results = await mock_vector_store.asimilarity_search("query", k=5)
    """
    from unittest.mock import AsyncMock
    from langchain_core.documents import Document

    vector_store = AsyncMock()

    # Mock similarity search - zwraca sample documents
    async def mock_similarity_search(query: str, k: int = 5):
        return [
            Document(
                page_content=f"Sample document {i} about {query}",
                metadata={
                    "doc_id": f"doc_{i}",
                    "title": f"Document {i}",
                    "chunk_index": i,
                }
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
    """
    Mock Neo4j Graph store dla testów GraphRAG bez Neo4j.

    Usage:
        def test_graph_rag(mock_graph_store):
            result = mock_graph_store.query("MATCH (n) RETURN n")
    """
    from unittest.mock import MagicMock

    graph_store = MagicMock()

    # Mock query - zwraca sample graph results (UPROSZCZONY SCHEMA - 5 properties)
    def mock_query(cypher: str, params: dict = None):
        # Return sample graph nodes
        return [
            {
                "type": "Wskaznik",
                "streszczenie": "Stopa zatrudnienia 78.4%",
                "skala": "78.4%",
                "pewnosc": "wysoka",
                "okres_czasu": "2022",
                "kluczowe_fakty": "wysoka stopa; młodzi dorośli; wykształcenie wyższe",
            },
            {
                "type": "Trend",
                "streszczenie": "Wzrost zatrudnienia młodych",
                "okres_czasu": "2018-2023",
                "kluczowe_fakty": "Wzrost o 12% w grupie 25-34",
            }
        ]

    graph_store.query = mock_query
    graph_store.get_schema = MagicMock(return_value="Mock graph schema")
    graph_store.add_graph_documents = MagicMock()

    return graph_store


@pytest.fixture
def sample_rag_document():
    """
    Przykładowy dokument RAG dla testów.

    Usage:
        def test_document_processing(sample_rag_document):
            assert sample_rag_document.title == "Test Report"
    """
    from langchain_core.documents import Document

    return Document(
        page_content="""
        Raport o polskim społeczeństwie 2023

        W Polsce w 2022 roku stopa zatrudnienia osób w wieku 25-34 lata
        z wyższym wykształceniem wyniosła 78.4% według danych GUS.

        Trendy demograficzne wskazują na wzrost mobilności zawodowej młodych
        dorosłych. W latach 2018-2023 obserwowano wzrost zatrudnienia o 12%
        w tej grupie wiekowej.

        Ceny mieszkań w Warszawie osiągnęły średnio 15000 zł za metr kwadratowy,
        co znacząco wpływa na decyzje mieszkaniowe młodych profesjonalistów.
        """,
        metadata={
            "title": "Raport GUS 2023",
            "country": "Poland",
            "year": "2023",
            "source": "GUS",
        }
    )


@pytest.fixture
def mock_gemini_2_5_pro():
    """
    Mock Gemini 2.5 Pro dla testów orchestration bez API.

    Usage:
        async def test_orchestration(mock_gemini_2_5_pro):
            response = await mock_gemini_2_5_pro.ainvoke("prompt")
            assert "groups" in response.content
    """
    from unittest.mock import AsyncMock
    from types import SimpleNamespace
    import json

    llm = AsyncMock()

    # Mock allocation plan response
    allocation_plan = {
        "total_personas": 20,
        "overall_context": (
            "Polskie społeczeństwo w 2024 roku charakteryzuje się wysoką stopą zatrudnienia "
            "młodych dorosłych z wyższym wykształceniem (78.4%). Jednocześnie ceny mieszkań "
            "w dużych miastach rosną szybciej niż dochody, co wpływa na decyzje życiowe."
        ),
        "groups": [
            {
                "count": 6,
                "demographics": {
                    "age": "25-34",
                    "gender": "kobieta",
                    "education": "wyższe",
                    "location": "Warszawa"
                },
                "brief": (
                    "Ta grupa stanowi około 17.3% populacji miejskiej według GUS 2022. "
                    "To fascynująca grupa społeczna która balansuje między budowaniem kariery "
                    "a decyzjami o rodzinie. Wskaźniki pokazują że 78.4% tej grupy jest "
                    "zatrudnionych - najwyższa stopa w Polsce. " * 10  # ~2000 chars
                ),
                "graph_insights": [
                    {
                        "type": "Wskaznik",
                        "summary": "Stopa zatrudnienia kobiet 25-34 z wyższym",
                        "magnitude": "78.4%",
                        "confidence": "high",
                        "time_period": "2022",
                        "source": "GUS",
                        "why_matters": "Wysoka stopa zatrudnienia oznacza purchasing power"
                    }
                ],
                "allocation_reasoning": "6 z 20 person (30%) bo grupa kluczowa dla early adoption"
            }
        ]
    }

    llm.ainvoke.return_value = SimpleNamespace(
        content=f"```json\n{json.dumps(allocation_plan, ensure_ascii=False, indent=2)}\n```"
    )

    return llm


@pytest.fixture
def mock_embeddings():
    """
    Mock Google Gemini embeddings dla testów bez API.

    Usage:
        def test_embeddings(mock_embeddings):
            embedding = mock_embeddings.embed_query("test")
            assert len(embedding) == 768
    """
    from unittest.mock import MagicMock
    import numpy as np

    embeddings = MagicMock()

    # Generate deterministic embeddings for testing
    def embed_query(text: str):
        np.random.seed(hash(text) % (2**32))
        return np.random.rand(768).tolist()

    def embed_documents(texts: list):
        return [embed_query(text) for text in texts]

    embeddings.embed_query = embed_query
    embeddings.embed_documents = embed_documents

    return embeddings


@pytest.fixture
def mock_concept_extraction():
    """
    Mock dla LLM concept extraction z tekstu.

    Usage:
        async def test_extraction(mock_concept_extraction):
            result = await mock_concept_extraction("Some text")
            assert "concepts" in result
    """
    from unittest.mock import AsyncMock

    async def extract_concepts(text: str):
        # Simple keyword-based extraction for deterministic tests
        words = text.lower().split()
        concepts = [w.capitalize() for w in words if len(w) > 5][:5]

        return {
            "concepts": concepts or ["General", "Topic"],
            "emotions": ["Neutral"],
            "sentiment": 0.0,
            "key_phrases": [text[:50]] if text else []
        }

    return AsyncMock(side_effect=extract_concepts)


@pytest_asyncio.fixture
async def rag_document_service_with_mocks(mock_vector_store, mock_graph_store, mock_embeddings):
    """
    RAGDocumentService z mockowanymi zależnościami.

    Usage:
        async def test_rag_service(rag_document_service_with_mocks):
            service = rag_document_service_with_mocks
            # service ma mocked Neo4j, embeddings, etc.
    """
    from app.services.rag_service import RAGDocumentService
    from unittest.mock import patch

    with patch('app.services.rag_service.GoogleGenerativeAIEmbeddings', return_value=mock_embeddings):
        service = RAGDocumentService()
        service.vector_store = mock_vector_store
        service.graph_store = mock_graph_store

        yield service


@pytest_asyncio.fixture
async def polish_society_rag_with_mocks(mock_vector_store, mock_embeddings):
    """
    PolishSocietyRAG z mockowanymi zależnościami.

    Usage:
        async def test_hybrid_search(polish_society_rag_with_mocks):
            rag = polish_society_rag_with_mocks
            results = await rag.hybrid_search("query", top_k=5)
    """
    from app.services.rag_service import PolishSocietyRAG
    from unittest.mock import patch

    with patch('app.services.rag_service.GoogleGenerativeAIEmbeddings', return_value=mock_embeddings):
        rag = PolishSocietyRAG()
        rag.vector_store = mock_vector_store
        rag._fulltext_index_initialized = True  # Skip index creation

        yield rag


@pytest_asyncio.fixture
async def graph_service_with_mocks(mock_neo4j_driver, mock_llm):
    """
    GraphService z mockowanymi zależnościami.

    Usage:
        async def test_graph_building(graph_service_with_mocks):
            service = graph_service_with_mocks
            await service.build_graph_from_focus_group(db, fg_id)
    """
    from app.services.graph_service import GraphService

    service = GraphService()
    service.driver = mock_neo4j_driver
    service.llm = mock_llm

    yield service


@pytest_asyncio.fixture
async def persona_orchestration_with_mocks(mock_gemini_2_5_pro, polish_society_rag_with_mocks):
    """
    PersonaOrchestrationService z mockowanymi zależnościami.

    Usage:
        async def test_orchestration(persona_orchestration_with_mocks):
            service = persona_orchestration_with_mocks
            plan = await service.create_persona_allocation_plan(...)
    """
    from app.services.persona_orchestration import PersonaOrchestrationService

    service = PersonaOrchestrationService()
    service.llm = mock_gemini_2_5_pro
    service.rag_service = await polish_society_rag_with_mocks

    yield service
