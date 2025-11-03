"""
App Loader - Application-wide configuration.

Ten moduł dostarcza:
- RedisConfig: Konfiguracja połączenia Redis
- DatabaseConfig: Konfiguracja PostgreSQL
- Neo4jConfig: Konfiguracja Neo4j
- AppConfig: Główna konfiguracja aplikacji (CORS, security, storage)

Użycie:
    from config import app

    # Redis
    redis_url = app.redis.url
    max_connections = app.redis.max_connections

    # Database
    db_url = app.database.url

    # App settings
    project_name = app.project_name
    api_prefix = app.api_prefix
"""

import logging
import os
from dataclasses import dataclass

from config.loader import ConfigLoader

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# DATACLASSES - INFRASTRUCTURE CONFIG
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class RedisConfig:
    """
    Konfiguracja połączenia Redis.

    Attributes:
        url: Redis connection string (z env: REDIS_URL)
        max_connections: Maksymalna liczba połączeń w pool
        socket_timeout: Timeout dla socket operations (sekundy)
        socket_keepalive: Włącz socket keepalive
        health_check_interval: Interval health check (sekundy)
        retry_on_timeout: Ponów próbę przy timeout
        max_retries: Maksymalna liczba prób
        retry_backoff: Backoff między próbami (sekundy)
    """
    url: str = "redis://localhost:6379/0"
    max_connections: int = 50
    socket_timeout: int = 5
    socket_keepalive: bool = True
    health_check_interval: int = 30
    retry_on_timeout: bool = True
    max_retries: int = 3
    retry_backoff: float = 0.5


@dataclass
class DatabaseConfig:
    """
    Konfiguracja PostgreSQL.

    Attributes:
        url: Database connection string (z env: DATABASE_URL)
        user: Database user (z env: POSTGRES_USER)
        password: Database password (z env: POSTGRES_PASSWORD)
        db_name: Database name (z env: POSTGRES_DB)
    """
    url: str = "postgresql+asyncpg://sight:dev_password_change_in_prod@localhost:5433/sight_db"
    user: str | None = None
    password: str | None = None
    db_name: str | None = None


@dataclass
class CeleryConfig:
    """
    Konfiguracja Celery Task Queue (opcjonalna).

    Attributes:
        broker_url: Celery broker URL (z env: CELERY_BROKER_URL)
        result_backend: Celery result backend (z env: CELERY_RESULT_BACKEND)
    """
    broker_url: str | None = None
    result_backend: str | None = None


@dataclass
class DocumentStorageConfig:
    """
    Konfiguracja document storage.

    Attributes:
        path: Ścieżka do katalogu z dokumentami
        max_size_mb: Maksymalny rozmiar uploadowanego dokumentu (MB)
    """
    path: str = "data/documents"
    max_size_mb: int = 50


@dataclass
class Neo4jConfig:
    """
    Konfiguracja Neo4j Graph Database.

    Attributes:
        uri: Neo4j connection URI (z env: NEO4J_URI)
        user: Neo4j user (z env: NEO4J_USER)
        password: Neo4j password (z env: NEO4J_PASSWORD)
        max_pool_size: Max connections per Cloud Run instance
        connection_timeout: TCP connection timeout (seconds)
        max_retry_time: Max time to retry transient failures (seconds)
    """
    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "dev_password_change_in_prod"
    max_pool_size: int = 50
    connection_timeout: int = 10
    max_retry_time: int = 30


# ═══════════════════════════════════════════════════════════════════════════
# APP CONFIG
# ═══════════════════════════════════════════════════════════════════════════


class AppConfig:
    """
    Główna konfiguracja aplikacji.

    Ładuje: config/app.yaml

    Features:
    - Environment variables override YAML values
    - Typed dataclasses dla infrastructure config
    - Sensowne defaulty dla development
    """

    def __init__(self, app_file: str = "app.yaml"):
        self.loader = ConfigLoader()
        self.config = self.loader.load_with_env_overrides(app_file)

        # Load app settings
        self.project_name = self.config.get("project_name", "Sight")
        self.api_version = self.config.get("api_version", "v1")
        self.api_prefix = self.config.get("api_prefix", "/api/v1")

        # Environment
        self.environment = self.config.get("environment", "development")
        self.debug = self.config.get("debug", True)

        # CORS
        self.allowed_origins = self.config.get("allowed_origins", [
            "http://localhost:5173",
            "http://localhost:3000",
        ])

        # Security
        self.secret_key = os.getenv(
            self.config.get("secret_key_env", "SECRET_KEY"),
            "dev_secret_key_CHANGE_IN_PRODUCTION"
        )
        self.algorithm = self.config.get("algorithm", "HS256")
        self.access_token_expire_minutes = self.config.get("access_token_expire_minutes", 30)

        # Load infrastructure configs
        self.redis = self._load_redis()
        self.database = self._load_database()
        self.neo4j = self._load_neo4j()
        self.celery = self._load_celery()
        self.document_storage = self._load_document_storage()

    def _load_redis(self) -> RedisConfig:
        """
        Ładuje Redis configuration.

        Returns:
            RedisConfig object z env overrides
        """
        redis_config = self.config.get("redis", {})

        # Get URL from env
        redis_url_env = redis_config.get("url_env", "REDIS_URL")
        redis_url = os.getenv(redis_url_env, redis_config.get("default_url", "redis://localhost:6379/0"))

        return RedisConfig(
            url=redis_url,
            max_connections=redis_config.get("max_connections", 50),
            socket_timeout=redis_config.get("socket_timeout", 5),
            socket_keepalive=redis_config.get("socket_keepalive", True),
            health_check_interval=redis_config.get("health_check_interval", 30),
            retry_on_timeout=redis_config.get("retry_on_timeout", True),
            max_retries=redis_config.get("max_retries", 3),
            retry_backoff=redis_config.get("retry_backoff", 0.5),
        )

    def _load_database(self) -> DatabaseConfig:
        """
        Ładuje Database configuration.

        Returns:
            DatabaseConfig object z env overrides
        """
        db_config = self.config.get("database", {})

        # Get DB URL from env
        db_url_env = db_config.get("url_env", "DATABASE_URL")
        db_url = os.getenv(
            db_url_env,
            db_config.get("default_url", "postgresql+asyncpg://sight:password@localhost:5432/sight_db")
        )

        # Get credentials from env
        user_env = db_config.get("user_env", "POSTGRES_USER")
        password_env = db_config.get("password_env", "POSTGRES_PASSWORD")
        db_name_env = db_config.get("db_env", "POSTGRES_DB")

        return DatabaseConfig(
            url=db_url,
            user=os.getenv(user_env),
            password=os.getenv(password_env),
            db_name=os.getenv(db_name_env),
        )

    def _load_neo4j(self) -> Neo4jConfig:
        """
        Ładuje Neo4j configuration.

        Returns:
            Neo4jConfig object z env overrides
        """
        neo4j_config = self.config.get("neo4j", {})

        # Get Neo4j credentials from env
        uri_env = neo4j_config.get("uri_env", "NEO4J_URI")
        user_env = neo4j_config.get("user_env", "NEO4J_USER")
        password_env = neo4j_config.get("password_env", "NEO4J_PASSWORD")

        return Neo4jConfig(
            uri=os.getenv(uri_env, neo4j_config.get("default_uri", "bolt://localhost:7687")),
            user=os.getenv(user_env, "neo4j"),
            password=os.getenv(password_env, "dev_password_change_in_prod"),
            max_pool_size=neo4j_config.get("max_pool_size", 50),
            connection_timeout=neo4j_config.get("connection_timeout", 10),
            max_retry_time=neo4j_config.get("max_retry_time", 30),
        )

    def _load_celery(self) -> CeleryConfig:
        """
        Ładuje Celery configuration.

        Returns:
            CeleryConfig object z env overrides
        """
        celery_config = self.config.get("celery", {})

        # Get Celery URLs from env (optional)
        broker_url_env = celery_config.get("broker_url_env", "CELERY_BROKER_URL")
        result_backend_env = celery_config.get("result_backend_env", "CELERY_RESULT_BACKEND")

        return CeleryConfig(
            broker_url=os.getenv(broker_url_env),
            result_backend=os.getenv(result_backend_env),
        )

    def _load_document_storage(self) -> DocumentStorageConfig:
        """
        Ładuje Document Storage configuration.

        Returns:
            DocumentStorageConfig object z env overrides
        """
        storage_config = self.config.get("document_storage", {})

        return DocumentStorageConfig(
            path=storage_config.get("path", "data/documents"),
            max_size_mb=storage_config.get("max_size_mb", 50),
        )


# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

# Global app singleton (lazy-initialized on first access)
_app: AppConfig | None = None


def get_app_config() -> AppConfig:
    """
    Get global AppConfig singleton.

    Returns:
        AppConfig instance
    """
    global _app
    if _app is None:
        _app = AppConfig()
        logger.debug("Initialized AppConfig singleton")
    return _app


# Convenience export
app = get_app_config()
