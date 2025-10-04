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
engine = create_async_engine(
    settings.DATABASE_URL,  # URL z pliku .env (postgresql+asyncpg://...)
    echo=settings.DEBUG,  # Loguj SQL queries w trybie DEBUG
    poolclass=NullPool if settings.ENVIRONMENT == "test" else None,  # Bez poolingu w testach
    pool_pre_ping=True,  # Sprawdzaj czy connection jest żywe przed użyciem
    pool_size=5 if settings.ENVIRONMENT == "production" else 5,  # Max 5 aktywnych połączeń
    max_overflow=10 if settings.ENVIRONMENT == "production" else 10,  # Max 10 dodatkowych przy szczycie
    pool_recycle=3600,  # Odtwarzaj połączenia co 1h (zapobiega timeout PostgreSQL)
)

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