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
