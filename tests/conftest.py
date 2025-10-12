"""
Pytest configuration and shared fixtures.

Ten plik zawiera fixtures używane przez wiele testów.
"""

import pytest
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

@pytest.fixture(scope="session")
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


@pytest.fixture
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

@pytest.fixture
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


@pytest.fixture
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

    client, user, headers = authenticated_client

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


@pytest.fixture
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

    project, personas, client, headers = project_with_personas

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
