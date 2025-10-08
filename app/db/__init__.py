"""
Moduł Database - Warstwa Dostępu do Bazy Danych

Zawiera:
- Base: Klasa bazowa SQLAlchemy dla wszystkich modeli ORM
- engine: Silnik asynchroniczny SQLAlchemy (asyncpg driver)
- AsyncSessionLocal: Factory do tworzenia sesji asynchronicznych
- get_db(): Dependency injection dla FastAPI - dostarcza sesję DB z automatycznym commit/rollback

Architektura:
PostgreSQL z asyncpg driver → SQLAlchemy async engine → AsyncSession → FastAPI endpoints

Użycie w API:
    @app.get("/items")
    async def get_items(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Item))
        return result.scalars().all()
"""

from .base import Base
from .session import get_db, AsyncSessionLocal, engine

__all__ = ["Base", "get_db", "AsyncSessionLocal", "engine"]