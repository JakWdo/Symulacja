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

import json
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from config import app as app_config
from app.core.logging_config import configure_logging
from app.core.scheduler import init_scheduler, shutdown_scheduler
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.api import project_crud, project_demographics, personas, focus_groups, analysis, surveys, auth, settings as settings_router, rag, dashboard, workflows, internal, study_designer, admin
from app.api.dependencies import get_current_admin_user, get_db
from app.api.exception_handlers import register_exception_handlers
from app.services.maintenance.cleanup_service import CleanupService
import logging
import os
import mimetypes

# Configure structured logging BEFORE creating any loggers
configure_logging(
    structured=app_config.environment == "production",
    level=os.getenv("LOG_LEVEL", "DEBUG" if app_config.debug else "INFO"),
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager - inicjalizacja/cleanup zasobów przy starcie/stopie aplikacji."""
    # Startup
    logger.info("🚀 LIFESPAN: Inicjalizacja aplikacji...")

    # DISABLED: Eager initialization RAG services (causes crash in Cloud Run with Google API)
    # RAG services będą inicjalizowane lazy (przy pierwszym użyciu) aby uniknąć:
    # - "503 Illegal metadata" błędów z Google Gemini API podczas startu
    # - Timeouts w Cloud Run health checks
    # - Niepotrzebnych wywołań API gdy RAG nie jest używany
    logger.info("✓ LIFESPAN: RAG services skonfigurowane (lazy initialization)")

    # Initialize APScheduler for background jobs
    init_scheduler()

    logger.info("✓ LIFESPAN: Aplikacja gotowa do obsługi żądań")

    yield

    # Shutdown
    logger.info("👋 LIFESPAN: Zamykanie aplikacji...")

    # Shutdown scheduler gracefully
    shutdown_scheduler(wait=True)

# Walidacja krytycznych ustawień w produkcji
if app_config.environment == "production":
    # Security: Walidacja SECRET_KEY
    secret_key = os.getenv("SECRET_KEY", app_config.secret_key)
    if secret_key == "change-me":
        raise ValueError(
            "SECRET_KEY must be changed in production! "
            "Generate a secure key with: openssl rand -hex 32"
        )
    if len(secret_key) < 32:
        raise ValueError(
            "SECRET_KEY must be at least 32 characters in production! "
            f"Current length: {len(secret_key)}. "
            "Generate a secure key with: openssl rand -hex 32"
        )
    # Warn jeśli SECRET_KEY wygląda słabo (tylko alfanumeryczne znaki)
    if secret_key.isalnum():
        logger.warning(
            "SECRET_KEY appears weak (only alphanumeric). "
            "Consider using special characters for better security. "
            "Generate with: openssl rand -hex 32"
        )

    # Security: Walidacja database passwords
    db_url = os.getenv("DATABASE_URL", app_config.database.url)
    if "password" in db_url.lower() or "dev_password" in db_url.lower():
        raise ValueError(
            "Default database password detected in production! "
            "Please use secure passwords."
        )

app = FastAPI(
    title=app_config.project_name,
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
if app_config.environment == "development":
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

# Request ID Middleware - FIRST (correlation tracking dla wszystkich requestów)
# Dodaje unikalny request_id do każdego requesta (propagowany przez contextvars)
app.add_middleware(RequestIDMiddleware)

# Security Headers Middleware
# Dodaje OWASP-recommended headers: X-Frame-Options, CSP, X-Content-Type-Options, etc.
enable_hsts = app_config.environment == "production"  # HSTS tylko na HTTPS w produkcji
app.add_middleware(SecurityHeadersMiddleware, enable_hsts=enable_hsts)

# Podpinamy katalog plików statycznych (avatary)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Podłącz routery z poszczególnych modułów
# Prefix: /api/v1 (z app_config.api_prefix)
# Endpointy autoryzacyjne jako pierwsze (publiczne)
app.include_router(auth.router, prefix=app_config.api_prefix, tags=["Auth"])

# Chronione endpointy (wymagają uwierzytelnienia)
# Projekty - podzielone na CRUD i soft delete operations
app.include_router(project_crud.router, prefix=app_config.api_prefix)
app.include_router(project_demographics.router, prefix=app_config.api_prefix)
app.include_router(personas.router, prefix=app_config.api_prefix, tags=["Personas"])
app.include_router(focus_groups.router, prefix=app_config.api_prefix, tags=["Focus Groups"])
app.include_router(surveys.router, prefix=app_config.api_prefix, tags=["Surveys"])
app.include_router(analysis.router, prefix=app_config.api_prefix, tags=["Analysis"])
app.include_router(rag.router, prefix=app_config.api_prefix)  # RAG już ma prefix="/rag" i tags w routerze
app.include_router(settings_router.router, prefix=app_config.api_prefix, tags=["Settings"])
app.include_router(dashboard.router, prefix=app_config.api_prefix, tags=["Dashboard"])
app.include_router(workflows.router, prefix=app_config.api_prefix, tags=["Workflows"])
app.include_router(study_designer.router, prefix=app_config.api_prefix, tags=["Study Designer"])

# Admin endpoints (wymagają roli ADMIN)
app.include_router(admin.router, prefix=app_config.api_prefix, tags=["Admin"])

# Internal endpoints (dla Cloud Tasks callbacks)
app.include_router(internal.router, tags=["Internal"])


# Root endpoint removed - SPA catch-all route handles "/" in production
# API info available at /health and /docs


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint - dla Cloud Run, Kubernetes, Docker, monitoring

    Sprawdza połączenia do kluczowych serwisów:
    - PostgreSQL (database)
    - Redis (cache)
    - Neo4j (graph database)

    Returns:
        Status: 200 (healthy/degraded), 503 (unhealthy)
        Body: {
            "status": "healthy" | "degraded" | "unhealthy",
            "environment": "production" | "staging" | "development",
            "checks": {
                "database": {...},
                "redis": {...},
                "neo4j": {...}
            },
            "latency_total_ms": float
        }

    Notes:
        - degraded: 1 service down, application still functional
        - unhealthy: 2+ services down, triggers rollback in Cloud Run
    """
    from fastapi import Response
    from app.services.shared.infrastructure_health import InfrastructureHealthService
    from app.core.redis import get_redis_client

    # Get Redis client
    redis_client = await get_redis_client()

    # Create health service
    health_service = InfrastructureHealthService(
        db=db,
        redis_client=redis_client
    )

    # Check all services (timeout 2s per service)
    health_result = await health_service.check_all(timeout=2.0)

    # Return 503 if unhealthy, 200 otherwise
    status_code = 503 if health_result["status"] == "unhealthy" else 200

    response_body = {
        "status": health_result["status"],
        "environment": app_config.environment,
        "checks": health_result["checks"],
        "latency_total_ms": health_result["latency_total_ms"],
    }

    return Response(
        content=json.dumps(response_body),
        status_code=status_code,
        media_type="application/json"
    )


@app.post("/admin/cleanup", tags=["Admin"])
async def manual_cleanup(
    db: AsyncSession = Depends(get_db),
    _current_admin=Depends(get_current_admin_user),
):
    """
    Manual cleanup trigger endpoint - dla testowania i emergency cleanup.

    Usuwa (hard delete) wszystkie soft-deleted entities starsze niż 7 dni.
    Ten process jest **nieodwracalny**.

    Returns:
        dict: Statystyki usuniętych entities
            {
                "status": "success",
                "stats": {
                    "projects_deleted": 5,
                    "personas_deleted": 45,
                    "focus_groups_deleted": 12,
                    "surveys_deleted": 3,
                    "total_deleted": 65
                },
                "cutoff_date": "2025-10-21T14:30:00",
                "retention_days": 7
            }

    Security:
        - TODO: Add authentication/authorization (admin only)
        - W produkcji dodaj rate limiting lub całkowicie wyłącz endpoint
    """
    logger.info("🔧 Manual cleanup triggered via /admin/cleanup endpoint")

    try:
        service = CleanupService(retention_days=7)
        stats = await service.cleanup_old_deleted_entities(db)

        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=7)

        logger.info(
            f"✅ Manual cleanup completed: {stats['total_deleted']} entities deleted",
            extra={
                "trigger": "manual",
                "stats": stats,
                "retention_days": 7,
            }
        )

        return {
            "status": "success",
            "stats": stats,
            "cutoff_date": cutoff_date.isoformat(),
            "retention_days": 7,
        }

    except Exception as exc:
        logger.error(f"❌ Manual cleanup failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup job failed: {str(exc)}"
        )


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
        from app.services.rag.clients.rag_clients import _connect_with_retry
        from neo4j import GraphDatabase

        def test_neo4j_connection():
            """Test Neo4j connection with quick timeout."""
            driver = GraphDatabase.driver(
                os.getenv("NEO4J_URI", app_config.neo4j.uri),
                auth=(
                    os.getenv("NEO4J_USER", app_config.neo4j.user),
                    os.getenv("NEO4J_PASSWORD", app_config.neo4j.password)
                ),
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


# Register exception handlers
register_exception_handlers(app)


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
