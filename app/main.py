"""
Główna aplikacja FastAPI - Market Research SaaS

System do przeprowadzania wirtualnych grup fokusowych z wykorzystaniem AI.
Wykorzystuje Google Gemini do generowania person i symulacji dyskusji.

Kluczowe endpointy:
- /projects - zarządzanie projektami badawczymi
- /personas - generowanie i zarządzanie personami
- /focus-groups - tworzenie i uruchamianie grup fokusowych
- /surveys - ankiety syntetyczne z odpowiedziami od person
- /analysis - analiza wyników i podsumowania AI
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.core.config import get_settings
from app.api import projects, personas, focus_groups, analysis, surveys, graph_analysis, auth
import logging

logger = logging.getLogger(__name__)

settings = get_settings()

# Walidacja krytycznych ustawień w produkcji
if settings.ENVIRONMENT == "production":
    if settings.SECRET_KEY == "change-me":
        raise ValueError(
            "SECRET_KEY must be changed in production! "
            "Generate a secure key with: openssl rand -hex 32"
        )
    if "password" in settings.DATABASE_URL.lower() or "dev_password" in settings.DATABASE_URL.lower():
        raise ValueError(
            "Default database password detected in production! "
            "Please use secure passwords."
        )

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered market research platform with synthetic personas",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware CORS - ograniczenie origin w zależności od środowiska
# Tryb deweloperski: wszystkie originy dozwolone (*)
# Tryb produkcyjny: tylko originy z ALLOWED_ORIGINS (np. https://app.example.com)
allowed_origins = (
    ["*"] if settings.ENVIRONMENT == "development"
    else settings.ALLOWED_ORIGINS.split(",")
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Lista dozwolonych origin
    allow_credentials=True,  # Zezwalamy na ciasteczka i nagłówki uwierzytelniające
    allow_methods=["*"],  # Wszystkie metody HTTP (GET, POST, PUT, DELETE itp.)
    allow_headers=["*"],  # Wszystkie nagłówki
)

# Podpinamy katalog plików statycznych (avatary)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Podłącz routery z poszczególnych modułów
# Prefix: /api/v1 (z settings.API_V1_PREFIX)
# Endpointy autoryzacyjne jako pierwsze (publiczne)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX, tags=["Auth"])

# Chronione endpointy (wymagają uwierzytelnienia)
app.include_router(projects.router, prefix=settings.API_V1_PREFIX, tags=["Projects"])
app.include_router(personas.router, prefix=settings.API_V1_PREFIX, tags=["Personas"])
app.include_router(focus_groups.router, prefix=settings.API_V1_PREFIX, tags=["Focus Groups"])
app.include_router(surveys.router, prefix=settings.API_V1_PREFIX, tags=["Surveys"])
app.include_router(analysis.router, prefix=settings.API_V1_PREFIX, tags=["Analysis"])
app.include_router(graph_analysis.router, prefix=settings.API_V1_PREFIX, tags=["Graph Analysis"])


@app.get("/")
async def root():
    """
    Root endpoint - informacje o API

    Returns:
        Podstawowe informacje o systemie i link do dokumentacji
    """
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",  # Interfejs Swagger
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint - do monitorowania (Kubernetes, Docker, etc.)

    Returns:
        Status zdrowia aplikacji i środowisko
    """
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


# Globalny handler wyjątków - łapie wszystkie nieobsłużone błędy
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Obsłuż wszystkie nieobsłużone wyjątki

    Zapobiega wyciekom szczegółów błędów w produkcji.
    W development zwraca pełny stack trace, w production tylko ogólny komunikat.

    Args:
        request: FastAPI Request
        exc: Wyjątek który nie został obsłużony

    Returns:
        JSONResponse z kodem 500 i bezpiecznym komunikatem błędu
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            # W DEBUG pokazuj szczegóły, w produkcji ukryj
            "error": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )
