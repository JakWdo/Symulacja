"""
Konfiguracja sesji bazy danych PostgreSQL (async)

Ten moduł zarządza połączeniami z bazą danych:
- engine - silnik SQLAlchemy (async) do wykonywania zapytań
- AsyncSessionLocal - factory do tworzenia sesji bazy danych
- get_db() - dependency dla FastAPI do wstrzykiwania sesji

Używa async SQLAlchemy dla wydajności (non-blocking I/O).
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import get_settings

settings = get_settings()

# Tworzenie silnika async z connection poolingiem
# Engine to główny punkt wejścia do bazy danych
#
# WAŻNE: Parametry poolingu (pool_size, max_overflow, pool_pre_ping, pool_recycle)
# są obsługiwane TYLKO przez PostgreSQL/MySQL z pełnym connection pooling.
# NIE działają z:
# - NullPool (używany w testach - ENVIRONMENT=test)
# - SQLite (używany w Cloud Build unit tests)
#
# Dlatego budujemy engine_kwargs conditionally:
use_null_pool = settings.ENVIRONMENT == "test"
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine_kwargs = {
    "url": settings.DATABASE_URL,
    "echo": settings.DEBUG,
}

# Dodaj parametry poolingu TYLKO dla PostgreSQL w production/development
if use_null_pool or is_sqlite:
    # Test environment lub SQLite - tylko NullPool (bez poolingu)
    engine_kwargs["poolclass"] = NullPool
else:
    # PostgreSQL w production/development - full connection pooling
    engine_kwargs.update({
        "pool_pre_ping": True,  # Sprawdzaj czy połączenie jest aktywne przed użyciem
        "pool_size": 5,  # Max 5 aktywnych połączeń
        "max_overflow": 10,  # Max 10 dodatkowych przy szczycie
        "pool_recycle": 3600,  # Odtwarzaj połączenia co 1h (zapobiega timeout PostgreSQL)
    })

engine = create_async_engine(**engine_kwargs)

# Factory do tworzenia sesji asynchronicznych
# Session = jednostka pracy (transaction, query, flush)
AsyncSessionLocal = async_sessionmaker(
    engine,  # Użyj engine zdefiniowanego powyżej
    class_=AsyncSession,  # Zwracaj obiekty AsyncSession
    expire_on_commit=False,  # Nie odświeżaj obiektów po commit (lepsze dla async)
    autocommit=False,  # Wymagaj jawnego commit()
    autoflush=False,  # Wymagaj jawnego flush()
)


async def get_db() -> AsyncSession:
    """
    Dependency dla FastAPI - dostarcza sesję bazy danych

    Użycie w endpointach:
        @app.get("/projects")
        async def get_projects(db: AsyncSession = Depends(get_db)):
            projects = await db.execute(select(Project))
            return projects.scalars().all()

    Działanie:
    1. Tworzy nową sesję z AsyncSessionLocal
    2. Yield zwraca sesję do endpointu (dependency injection)
    3. Finally zamyka sesję po zakończeniu requestu (nawet jeśli błąd)

    To gwarantuje:
    - Każdy request ma swoją sesję
    - Sesje są zawsze zamykane (brak wycieków)
    - Bezpieczne współdzielenie pool connectionów
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session  # Zwróć sesję do endpointu
        finally:
            await session.close()  # Zawsze zamknij sesję (nawet przy błędzie)
