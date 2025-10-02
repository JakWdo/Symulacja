from typing import Optional
from functools import lru_cache

try:
    from pydantic_settings import BaseSettings
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    from pydantic import BaseSettings  # type: ignore


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://market_research:password@localhost:5432/market_research_db"
    POSTGRES_USER: str = "market_research"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "market_research_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # LLM APIs
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    # Application
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Persona Generation
    DEFAULT_LLM_PROVIDER: str = "google"  # google, openai, anthropic
    PERSONA_GENERATION_MODEL: str = "gemini-2.5-flash"
    ANALYSIS_MODEL: str = "gemini-2.5-pro"
    DEFAULT_MODEL: str = "gemini-2.5-flash"  # Backwards compatibility
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 8000

    # Performance Targets
    MAX_RESPONSE_TIME_PER_PERSONA: int = 3
    MAX_FOCUS_GROUP_TIME: int = 30
    CONSISTENCY_ERROR_THRESHOLD: float = 0.05
    STATISTICAL_SIGNIFICANCE_THRESHOLD: float = 0.05
    RANDOM_SEED: int = 42

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Market Research SaaS"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"  # Comma-separated list

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()
