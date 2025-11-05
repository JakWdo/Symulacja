"""Database fixtures used by integration and e2e tests."""

from collections.abc import AsyncGenerator
import os

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from config import app as app_config
from app.db.base import Base


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """
    Provide an isolated async SQLAlchemy engine against the test database.

    The engine rebuilds the schema for every test session and drops all tables
    afterwards so CI runs always start from a clean slate.
    """
    # Use new config system (PR4)
    db_url = os.getenv("DATABASE_URL", app_config.database.url)
    test_db_url = db_url.replace("/sight_db", "/test_sight_db")

    engine = create_async_engine(
        test_db_url,
        echo=False,
        poolclass=NullPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Yield AsyncSession that allows commits (services commit by themselves).

    Nie używamy rollback pattern, ponieważ serwisy commitują same.
    Test database jest czyszczona na początku każdej sesji testowej.
    """
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session
        # Serwisy commitują same - nie robimy rollback tutaj
