from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Database
    DATABASE_URL: str
    POSTGRES_USER: str = "market_research"
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "market_research_db"

    # Redis
    REDIS_URL: str

    # Neo4j
    NEO4J_URI: str
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str

    # LLM APIs
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    # Application
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Persona Generation
    DEFAULT_LLM_PROVIDER: str = "google"  # google, openai, anthropic
    DEFAULT_MODEL: str = "gemini-2.0-flash-exp"  # gemini-2.0-flash-exp or gemini-1.5-pro
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 8000

    # Performance Targets
    MAX_RESPONSE_TIME_PER_PERSONA: int = 3
    MAX_FOCUS_GROUP_TIME: int = 30
    CONSISTENCY_ERROR_THRESHOLD: float = 0.05
    STATISTICAL_SIGNIFICANCE_THRESHOLD: float = 0.05

    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Market Research SaaS"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()