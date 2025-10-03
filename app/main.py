"""
Główna aplikacja FastAPI - Market Research SaaS

System do przeprowadzania wirtualnych grup fokusowych z wykorzystaniem AI.
Wykorzystuje Google Gemini do generowania person i symulacji dyskusji.

Kluczowe endpointy:
- /projects - zarządzanie projektami badawczymi
- /personas - generowanie i zarządzanie personami
- /focus-groups - tworzenie i uruchamianie grup fokusowych
- /analysis - analiza wyników i podsumowania AI
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import get_settings
from app.api import projects, personas, focus_groups, analysis
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
    description="AI-powered market research SaaS platform with synthetic personas",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware - restrict origins based on environment
allowed_origins = (
    ["*"] if settings.ENVIRONMENT == "development"
    else settings.ALLOWED_ORIGINS.split(",")
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router, prefix=settings.API_V1_PREFIX, tags=["Projects"])
app.include_router(personas.router, prefix=settings.API_V1_PREFIX, tags=["Personas"])
app.include_router(focus_groups.router, prefix=settings.API_V1_PREFIX, tags=["Focus Groups"])
app.include_router(analysis.router, prefix=settings.API_V1_PREFIX, tags=["Analysis"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


# Global exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )