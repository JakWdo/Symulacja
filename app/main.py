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
from pathlib import Path
from fastapi import FastAPI, Request, status, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import get_settings
from app.middleware.security import SecurityHeadersMiddleware
from app.api import projects, personas, focus_groups, analysis, surveys, auth, settings as settings_router, rag
import logging
import os
import mimetypes

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
#
# IMPORTANT: W single service deployment (backend + frontend w tym samym kontenerze)
# CORS NIE JEST POTRZEBNY w production, bo requests są same-origin:
# - Frontend: https://sight-XXX.run.app (serwowany przez FastAPI static files)
# - Backend: https://sight-XXX.run.app/api/v1/* (ten sam origin!)
# - Browser: Same-origin requests NIE WYMAGAJĄ CORS headers
#
# CORS jest potrzebny TYLKO w development, gdy frontend dev server (localhost:5173)
# robi requesty do backend (localhost:8000) - to są cross-origin requests.
if settings.ENVIRONMENT == "development":
    # Development: frontend na localhost:5173, backend na localhost:8000
    # To są cross-origin requests, wymagają CORS
    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,  # Lista dozwolonych origin
        allow_credentials=True,  # Zezwalamy na ciasteczka i nagłówki uwierzytelniające
        allow_methods=["*"],  # Wszystkie metody HTTP
        allow_headers=["*"],  # Wszystkie nagłówki
    )
    logger.info(f"🔓 CORS enabled for development origins: {allowed_origins}")
else:
    # Production: single service deployment (backend + frontend same origin)
    # Same-origin requests NIE WYMAGAJĄ CORS middleware
    # Security benefit: Mniejszy attack surface
    logger.info("🔒 CORS disabled for production (same-origin deployment)")

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
app.include_router(rag.router, prefix=settings.API_V1_PREFIX)  # RAG już ma prefix="/rag" i tags w routerze
app.include_router(settings_router.router, prefix=settings.API_V1_PREFIX, tags=["Settings"])


# Root endpoint removed - SPA catch-all route handles "/" in production
# API info available at /health and /docs


@app.get("/health")
async def health_check():
    """
    Liveness check - basic ping for Cloud Run health monitoring.

    Returns:
        Simple status indicating the application process is alive.
    """
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/ready")
async def readiness_check():
    """
    Readiness check - verify dependencies are available.

    Checks:
    - PostgreSQL connection
    - Redis connection (optional - degraded if unavailable)
    - Neo4j connection (optional - degraded if unavailable)

    Returns:
        Status of application and all dependencies.
        Status can be: "ready", "not_ready", "degraded"
    """
    from datetime import datetime
    from sqlalchemy import text

    status = {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {}
    }

    # Check PostgreSQL (REQUIRED)
    try:
        from app.db import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        status["dependencies"]["postgresql"] = {"status": "ok"}
    except Exception as exc:
        status["dependencies"]["postgresql"] = {"status": "failed", "error": str(exc)}
        status["status"] = "not_ready"

    # Check Redis (OPTIONAL - used for caching)
    try:
        from app.api.rag import redis_client
        if redis_client:
            await redis_client.ping()
            status["dependencies"]["redis"] = {"status": "ok"}
        else:
            status["dependencies"]["redis"] = {"status": "not_initialized"}
    except Exception as exc:
        status["dependencies"]["redis"] = {"status": "degraded", "error": str(exc)}
        # Redis optional - don't block readiness

    # Check Neo4j (OPTIONAL - used for RAG)
    try:
        from app.services.rag import get_vector_store
        import logging
        logger = logging.getLogger(__name__)
        vector_store = get_vector_store(logger)
        if vector_store:
            status["dependencies"]["neo4j"] = {"status": "ok"}
        else:
            status["dependencies"]["neo4j"] = {"status": "degraded", "error": "Vector store unavailable"}
    except Exception as exc:
        status["dependencies"]["neo4j"] = {"status": "degraded", "error": str(exc)}
        # Neo4j optional - don't block readiness

    # Check RAG services status
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

    status["rag_services"] = rag_status

    return status


@app.get("/startup")
async def startup_probe():
    """
    Startup probe endpoint - używany przez Cloud Run do sprawdzenia gotowości aplikacji.

    Sprawdza:
    - Połączenie z Neo4j (krytyczne dla RAG)
    - Inicjalizację podstawowych serwisów

    Returns:
        200 OK jeśli aplikacja jest gotowa do obsługi żądań
        503 Service Unavailable jeśli aplikacja nie jest jeszcze gotowa

    Note:
        Cloud Run czeka na 200 OK przed routing traffic do nowej rewizji.
        Timeout: 300s (5min) dla inicjalizacji Neo4j + RAG services.
    """
    checks = {
        "api": "ready",
        "neo4j": "unknown",
        "rag_services": "not_initialized"
    }

    try:
        # Sprawdź Neo4j connectivity (krytyczne dla RAG)
        from app.services.rag.rag_clients import _connect_with_retry
        from neo4j import GraphDatabase

        def test_neo4j_connection():
            """Test Neo4j connection with quick timeout."""
            driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                max_connection_lifetime=5,
            )
            driver.verify_connectivity()
            driver.close()
            return True

        # Quick connectivity check (1 retry, 2s timeout total)
        neo4j_ok = _connect_with_retry(
            test_neo4j_connection,
            logger,
            "Neo4j Startup Probe",
            max_retries=1,
            initial_delay=1.0
        )

        if neo4j_ok:
            checks["neo4j"] = "connected"
        else:
            checks["neo4j"] = "connection_failed"
            logger.warning("⚠️  Startup probe: Neo4j connection failed - RAG features may be unavailable")
            # NON-FATAL: App może startować bez Neo4j, RAG services mają własny retry logic
            # return JSONResponse(
            #     status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            #     content={"status": "not_ready", "checks": checks}
            # )

        # Sprawdź czy lazy-loaded RAG services są dostępne (nie inicjalizuj ich teraz!)
        from app.api.rag import _rag_document_service, _polish_society_rag
        if _rag_document_service is not None or _polish_society_rag is not None:
            checks["rag_services"] = "initialized"
        else:
            checks["rag_services"] = "lazy_load_ready"

    except Exception as exc:
        logger.error("❌ Startup probe error: %s", exc, exc_info=True)
        checks["error"] = str(exc)
        # App może działać bez RAG, więc nie blokujemy startu
        # return JSONResponse(
        #     status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        #     content={"status": "not_ready", "checks": checks, "error": str(exc)}
        # )

    # App jest ready - podstawowa funkcjonalność (auth, projects, etc.) działa bez RAG
    return {
        "status": "ready",
        "checks": checks,
        "note": "RAG services use lazy initialization - will initialize on first use"
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

    # Serve static files from root (logo.png, sight-logo-przezroczyste.png, etc.)
    # Note: This must be AFTER /assets mount but BEFORE catch-all route
    @app.get("/{filename}", include_in_schema=False)
    async def serve_static_root(filename: str):
        """Serve static files from root (logo.png, etc.)"""
        # Only serve files that exist in static/
        static_file = Path("static") / filename
        if static_file.exists() and static_file.is_file():
            # Determine content type
            content_type, _ = mimetypes.guess_type(str(static_file))
            with open(static_file, "rb") as f:
                return Response(content=f.read(), media_type=content_type or "application/octet-stream")
        # If file doesn't exist, let catch-all handle it
        raise HTTPException(status_code=404)

    # Catch-all route: serve index.html for React Router (SPA)
    # IMPORTANT: This MUST be the LAST route (after all API routes)
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_react_app(full_path: str):
        """
        Serve React SPA for all non-API routes.
        React Router handles client-side routing.
        """
        # Don't intercept API routes, health, docs, or static files
        if (
            full_path.startswith("api/")
            or full_path in ["health", "docs", "openapi.json", "redoc", "static"]
            or full_path.endswith((".png", ".jpg", ".jpeg", ".ico", ".svg", ".css", ".js", ".json", ".woff", ".woff2", ".ttf"))
        ):
            # Let FastAPI's normal 404 handler deal with this
            raise HTTPException(status_code=404, detail="Not found")

        # Serve index.html (React app entry point)
        return FileResponse("static/index.html")

    logger.info("✅ React SPA mounted at / (catch-all route)")
else:
    logger.info("⚠️  No static files found - running in API-only mode")
