"""
Tests for AppLoader - Application infrastructure configuration.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from config.app_loader import (
    AppConfig,
    RedisConfig,
    DatabaseConfig,
    Neo4jConfig,
    CeleryConfig,
    DocumentStorageConfig,
    get_app_config,
)


class TestRedisConfig:
    """Test Redis configuration loading."""

    @pytest.fixture
    def app(self):
        """Get app config."""
        return get_app_config()

    def test_redis_config_loaded(self, app):
        """Test that Redis config is loaded."""
        assert isinstance(app.redis, RedisConfig)

    def test_redis_url_from_env(self, app):
        """Test that Redis URL comes from environment or default."""
        assert isinstance(app.redis.url, str)
        assert app.redis.url.startswith("redis://")

    def test_redis_max_connections(self, app):
        """Test that max connections is set and reasonable."""
        assert isinstance(app.redis.max_connections, int)
        assert app.redis.max_connections > 0
        assert app.redis.max_connections <= 200  # Reasonable max

    def test_redis_socket_timeout(self, app):
        """Test that socket timeout is set."""
        assert isinstance(app.redis.socket_timeout, int)
        assert app.redis.socket_timeout > 0

    def test_redis_health_check_interval(self, app):
        """Test that health check interval is set."""
        assert isinstance(app.redis.health_check_interval, int)
        assert app.redis.health_check_interval > 0

    def test_redis_retry_settings(self, app):
        """Test that retry settings are configured."""
        assert isinstance(app.redis.retry_on_timeout, bool)
        assert isinstance(app.redis.max_retries, int)
        assert app.redis.max_retries > 0
        assert isinstance(app.redis.retry_backoff, float)
        assert app.redis.retry_backoff > 0


class TestDatabaseConfig:
    """Test Database configuration loading."""

    @pytest.fixture
    def app(self):
        """Get app config."""
        return get_app_config()

    def test_database_config_loaded(self, app):
        """Test that Database config is loaded."""
        assert isinstance(app.database, DatabaseConfig)

    def test_database_url_from_env(self, app):
        """Test that Database URL comes from environment or default."""
        assert isinstance(app.database.url, str)
        assert "postgresql" in app.database.url or "asyncpg" in app.database.url

    def test_database_credentials(self, app):
        """Test that database credentials can be set via env."""
        # These are optional (can be None if not set in env)
        assert app.database.user is None or isinstance(app.database.user, str)
        assert app.database.password is None or isinstance(app.database.password, str)
        assert app.database.db_name is None or isinstance(app.database.db_name, str)


class TestNeo4jConfig:
    """Test Neo4j configuration loading."""

    @pytest.fixture
    def app(self):
        """Get app config."""
        return get_app_config()

    def test_neo4j_config_loaded(self, app):
        """Test that Neo4j config is loaded."""
        assert isinstance(app.neo4j, Neo4jConfig)

    def test_neo4j_uri(self, app):
        """Test that Neo4j URI is set."""
        assert isinstance(app.neo4j.uri, str)
        assert "bolt://" in app.neo4j.uri or "neo4j://" in app.neo4j.uri

    def test_neo4j_credentials(self, app):
        """Test that Neo4j credentials are set."""
        assert isinstance(app.neo4j.user, str)
        assert isinstance(app.neo4j.password, str)

    def test_neo4j_connection_pool(self, app):
        """Test that connection pool settings are configured."""
        assert isinstance(app.neo4j.max_pool_size, int)
        assert app.neo4j.max_pool_size > 0
        assert app.neo4j.max_pool_size <= 200  # Reasonable max

    def test_neo4j_timeouts(self, app):
        """Test that timeout settings are configured."""
        assert isinstance(app.neo4j.connection_timeout, int)
        assert app.neo4j.connection_timeout > 0
        assert isinstance(app.neo4j.max_retry_time, int)
        assert app.neo4j.max_retry_time > 0


class TestCeleryConfig:
    """Test Celery configuration loading."""

    @pytest.fixture
    def app(self):
        """Get app config."""
        return get_app_config()

    def test_celery_config_loaded(self, app):
        """Test that Celery config is loaded."""
        assert isinstance(app.celery, CeleryConfig)

    def test_celery_optional_config(self, app):
        """Test that Celery URLs are optional (None if not in env)."""
        assert app.celery.broker_url is None or isinstance(app.celery.broker_url, str)
        assert app.celery.result_backend is None or isinstance(app.celery.result_backend, str)


class TestDocumentStorageConfig:
    """Test Document Storage configuration loading."""

    @pytest.fixture
    def app(self):
        """Get app config."""
        return get_app_config()

    def test_storage_config_loaded(self, app):
        """Test that storage config is loaded."""
        assert isinstance(app.document_storage, DocumentStorageConfig)

    def test_storage_path(self, app):
        """Test that storage path is set."""
        assert isinstance(app.document_storage.path, str)
        assert len(app.document_storage.path) > 0

    def test_storage_max_size(self, app):
        """Test that max size is set and reasonable."""
        assert isinstance(app.document_storage.max_size_mb, int)
        assert app.document_storage.max_size_mb > 0
        assert app.document_storage.max_size_mb <= 500  # Reasonable max


class TestAppSettings:
    """Test general app settings."""

    @pytest.fixture
    def app(self):
        """Get app config."""
        return get_app_config()

    def test_project_name(self, app):
        """Test that project name is set."""
        assert isinstance(app.project_name, str)
        assert len(app.project_name) > 0

    def test_api_version(self, app):
        """Test that API version is set."""
        assert isinstance(app.api_version, str)
        assert len(app.api_version) > 0

    def test_api_prefix(self, app):
        """Test that API prefix is set."""
        assert isinstance(app.api_prefix, str)
        assert app.api_prefix.startswith("/")

    def test_environment(self, app):
        """Test that environment is set."""
        assert isinstance(app.environment, str)
        assert app.environment in ["development", "staging", "production"]

    def test_debug_flag(self, app):
        """Test that debug flag is set."""
        assert isinstance(app.debug, bool)

    def test_allowed_origins(self, app):
        """Test that CORS origins are configured."""
        assert isinstance(app.allowed_origins, list)
        assert len(app.allowed_origins) > 0
        assert all(isinstance(origin, str) for origin in app.allowed_origins)


class TestSecuritySettings:
    """Test security-related settings."""

    @pytest.fixture
    def app(self):
        """Get app config."""
        return get_app_config()

    def test_secret_key(self, app):
        """Test that secret key is set."""
        assert isinstance(app.secret_key, str)
        assert len(app.secret_key) > 0

    def test_algorithm(self, app):
        """Test that JWT algorithm is set."""
        assert isinstance(app.algorithm, str)
        assert app.algorithm in ["HS256", "HS384", "HS512", "RS256"]

    def test_access_token_expire(self, app):
        """Test that token expiration is set."""
        assert isinstance(app.access_token_expire_minutes, int)
        assert app.access_token_expire_minutes > 0
        assert app.access_token_expire_minutes <= 1440  # Max 24 hours


class TestAppConfigSingleton:
    """Test singleton pattern and caching."""

    def test_singleton_returns_same_instance(self):
        """Test that get_app_config() returns the same instance."""
        config1 = get_app_config()
        config2 = get_app_config()

        assert config1 is config2, "Singleton should return same instance"

    def test_singleton_caches_nested_configs(self):
        """Test that nested configs are cached."""
        config1 = get_app_config()
        redis1 = config1.redis

        config2 = get_app_config()
        redis2 = config2.redis

        # Should be same object reference (cached)
        assert redis1 is redis2


class TestEnvironmentVariableOverrides:
    """Test that environment variables override YAML config."""

    @patch.dict(os.environ, {"REDIS_URL": "redis://custom:6380/1"})
    def test_redis_url_from_env_var(self):
        """Test that REDIS_URL env var overrides config."""
        # Need to create new instance to pick up env var
        config = AppConfig()

        assert config.redis.url == "redis://custom:6380/1"

    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://custom:5433/custom_db"})
    def test_database_url_from_env_var(self):
        """Test that DATABASE_URL env var overrides config."""
        config = AppConfig()

        assert "custom" in config.database.url

    @patch.dict(os.environ, {"NEO4J_URI": "bolt://custom:7688"})
    def test_neo4j_uri_from_env_var(self):
        """Test that NEO4J_URI env var overrides config."""
        config = AppConfig()

        assert "custom" in config.neo4j.uri

    @patch.dict(os.environ, {"SECRET_KEY": "test_secret_key_12345"})
    def test_secret_key_from_env_var(self):
        """Test that SECRET_KEY env var is used."""
        config = AppConfig()

        assert config.secret_key == "test_secret_key_12345"


class TestDataclassDefaults:
    """Test that dataclass default values work correctly."""

    def test_redis_config_defaults(self):
        """Test RedisConfig default values."""
        redis = RedisConfig()

        assert redis.url == "redis://localhost:6379/0"
        assert redis.max_connections == 50
        assert redis.socket_timeout == 5
        assert redis.socket_keepalive is True

    def test_database_config_defaults(self):
        """Test DatabaseConfig default values."""
        db = DatabaseConfig()

        assert "postgresql" in db.url or "asyncpg" in db.url
        assert db.user is None
        assert db.password is None

    def test_neo4j_config_defaults(self):
        """Test Neo4jConfig default values."""
        neo4j = Neo4jConfig()

        assert neo4j.uri == "bolt://localhost:7687"
        assert neo4j.user == "neo4j"
        assert neo4j.max_pool_size == 50

    def test_celery_config_defaults(self):
        """Test CeleryConfig default values."""
        celery = CeleryConfig()

        assert celery.broker_url is None
        assert celery.result_backend is None

    def test_document_storage_defaults(self):
        """Test DocumentStorageConfig default values."""
        storage = DocumentStorageConfig()

        assert storage.path == "data/documents"
        assert storage.max_size_mb == 50


class TestConfigDefaults:
    """Test default values when config file is missing or incomplete."""

    @patch("config.app_loader.ConfigLoader.load_with_env_overrides")
    def test_missing_redis_section_uses_defaults(self, mock_load):
        """Test that missing Redis section uses default values."""
        mock_load.return_value = {}  # Empty config

        config = AppConfig()

        assert config.redis.max_connections == 50
        assert config.redis.socket_timeout == 5

    @patch("config.app_loader.ConfigLoader.load_with_env_overrides")
    def test_missing_neo4j_section_uses_defaults(self, mock_load):
        """Test that missing Neo4j section uses defaults."""
        mock_load.return_value = {}

        config = AppConfig()

        assert config.neo4j.max_pool_size == 50
        assert config.neo4j.connection_timeout == 10
