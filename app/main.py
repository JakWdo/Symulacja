"""
Główna aplikacja FastAPI - Sight

System do przeprowadzania wirtualnych grup fokusowych z wykorzystaniem AI.
Wykorzystuje Google Gemini do generowania person i symulacji dyskusji.

Kluczowe endpointy:
- /projects - zarządzanie projektami badawczymi
- /personas - generowanie i zarządzanie personami
- /focus-groups - tworzenie i uruchamianie grup fokusowych
- /surveys - ankiety syntetyczne z odpowiedziami od person
- /analysis - analiza wyników i podsumowania AI
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import get_settings
from app.middleware.security import SecurityHeadersMiddleware
from app.api import projects, personas, focus_groups, analysis, surveys, graph_analysis, auth, settings as settings_router, rag
import logging
import os

logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager - inicjalizacja/cleanup zasobów przy starcie/stopie aplikacji."""
    # Startup
    print("🚀 LIFESPAN: Inicjalizacja aplikacji...")
    logger.info("🚀 LIFESPAN: Inicjalizacja aplikacji...")

    # DISABLED: Eager initialization RAG services (causes crash in Cloud Run with Google API)
    # RAG services będą inicjalizowane lazy (przy pierwszym użyciu) aby uniknąć:
    # - "503 Illegal metadata" błędów z Google Gemini API podczas startu
    # - Timeouts w Cloud Run health checks
    # - Niepotrzebnych wywołań API gdy RAG nie jest używany
    logger.info("✓ LIFESPAN: RAG services skonfigurowane (lazy initialization)")

    print("✓ LIFESPAN: Aplikacja gotowa do obsługi żądań")
    logger.info("✓ LIFESPAN: Aplikacja gotowa do obsługi żądań")

    yield

    # Shutdown
    print("👋 LIFESPAN: Zamykanie aplikacji...")
    logger.info("👋 LIFESPAN: Zamykanie aplikacji...")

# Walidacja krytycznych ustawień w produkcji
if settings.ENVIRONMENT == "production":
    # Security: Walidacja SECRET_KEY
    if settings.SECRET_KEY == "change-me":
        raise ValueError(
            "SECRET_KEY must be changed in production! "
            "Generate a secure key with: openssl rand -hex 32"
        )
    if len(settings.SECRET_KEY) < 32:
        raise ValueError(
            "SECRET_KEY must be at least 32 characters in production! "
            f"Current length: {len(settings.SECRET_KEY)}. "
            "Generate a secure key with: openssl rand -hex 32"
        )
    # Warn jeśli SECRET_KEY wygląda słabo (tylko alfanumeryczne znaki)
    if settings.SECRET_KEY.isalnum():
        logger.warning(
            "SECRET_KEY appears weak (only alphanumeric). "
            "Consider using special characters for better security. "
            "Generate with: openssl rand -hex 32"
        )

    # Security: Walidacja database passwords
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
    lifespan=lifespan,
)

# Setup Rate Limiting
# Security: Rate limiting chroni przed brute force, DoS i abuse API
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware CORS - ograniczenie origin w zależności od środowiska
# Security: NIE używaj wildcard ["*"] z credentials nawet w development
# Tryb deweloperski: localhost origins (frontend dev servers)
# Tryb produkcyjny: tylko originy z ALLOWED_ORIGINS (np. https://app.example.com)
allowed_origins = (
    ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"]
    if settings.ENVIRONMENT == "development"
    else settings.ALLOWED_ORIGINS.split(",")
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Lista dozwolonych origin
    allow_credentials=True,  # Zezwalamy na ciasteczka i nagłówki uwierzytelniające
    allow_methods=["*"],  # Wszystkie metody HTTP (GET, POST, PUT, DELETE itp.)
    allow_headers=["*"],  # Wszystkie nagłówki
)

# Security Headers Middleware
# Dodaje OWASP-recommended headers: X-Frame-Options, CSP, X-Content-Type-Options, etc.
enable_hsts = settings.ENVIRONMENT == "production"  # HSTS tylko na HTTPS w produkcji
app.add_middleware(SecurityHeadersMiddleware, enable_hsts=enable_hsts)

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
app.include_router(rag.router, prefix=settings.API_V1_PREFIX)  # RAG już ma prefix="/rag" i tags w routerze
app.include_router(settings_router.router, prefix=settings.API_V1_PREFIX, tags=["Settings"])


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
    # Diagnostyka RAG serwisów
    rag_status = {}
    try:
        from app.api.rag import _rag_document_service, _polish_society_rag
        rag_status["rag_document_service_initialized"] = _rag_document_service is not None
        rag_status["polish_society_rag_initialized"] = _polish_society_rag is not None
        if _rag_document_service:
            rag_status["rag_doc_vector_store_ok"] = _rag_document_service.vector_store is not None
            rag_status["rag_doc_graph_store_ok"] = _rag_document_service.graph_store is not None
        if _polish_society_rag:
            rag_status["polish_rag_vector_store_ok"] = _polish_society_rag.vector_store is not None
    except Exception as exc:
        rag_status["error"] = str(exc)

    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "rag_services": rag_status
    }


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


# ============================================================================
# STATIC FILES SERVING (Production: React SPA)
# ============================================================================
# Serve React static files ONLY in production (when static/ folder exists)
# In development, Vite dev server handles this (docker-compose)
# ============================================================================

if os.path.exists("static") and os.path.exists("static/index.html"):
    logger.info("🎨 Static files detected - mounting React SPA")

    # Mount /assets for JS, CSS, images (with cache headers)
    app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")

    # Catch-all route: serve index.html for React Router (SPA)
    # IMPORTANT: This MUST be the LAST route (after all API routes)
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_react_app(full_path: str):
        """
        Serve React SPA for all non-API routes.
        React Router handles client-side routing.
        """
        # Don't intercept API routes, health, docs
        if full_path.startswith("api/") or full_path in ["health", "docs", "openapi.json", "redoc", "static"]:
            # Let FastAPI's normal 404 handler deal with this
            raise HTTPException(status_code=404, detail="Not found")

        # Serve index.html (React app entry point)
        return FileResponse("static/index.html")

    logger.info("✅ React SPA mounted at / (catch-all route)")
else:
    logger.info("⚠️  No static files found - running in API-only mode")
