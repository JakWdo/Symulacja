"""Database fixtures used by integration and e2e tests."""

from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.db.base import Base


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """
    Provide an isolated async SQLAlchemy engine against the test database.

    The engine rebuilds the schema for every test session and drops all tables
    afterwards so CI runs always start from a clean slate.
    """
    settings = get_settings()
    test_db_url = settings.DATABASE_URL.replace("/sight_db", "/test_sight_db")

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
    Yield a transactional AsyncSession that automatically rolls back between tests.
    """
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        async with session.begin():
            yield session
            await session.rollback()
