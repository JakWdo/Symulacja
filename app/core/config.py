"""
Configuration settings - Adapter to centralized YAML config

⚠️ DEPRECATION NOTICE ⚠️

This module provides backward compatibility with the old Settings class.
All new code should use the centralized config system:

    # OLD (deprecated but still works):
    from app.core.config import get_settings
    settings = get_settings()
    db_url = settings.DATABASE_URL

    # NEW (recommended):
    from config import app, features, models
    db_url = app.database.url
    rag_enabled = features.rag.enabled
    model_config = models.get("personas", "generation")

Migration timeline:
- v1.0: Both approaches work
- v1.1: Deprecation warnings added (for LLM/RAG/Features only)
- v2.0: Old Settings class removed (planned)

See config/README.md for full migration guide.

⚠️ IMPLEMENTATION NOTE ⚠️

This class is an ADAPTER that delegates to config loaders from config/.
- Infrastructure (DB, Redis, Neo4j): No deprecation warnings (stable API)
- LLM Models: Deprecation warnings (migrate to config.models)
- RAG Settings: Deprecation warnings (migrate to config.rag)
- Feature Flags: Deprecation warnings (migrate to config.features)
"""

from functools import lru_cache
import os
import warnings

try:
    from pydantic_settings import BaseSettings
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    from pydantic import BaseSettings  # type: ignore


class Settings(BaseSettings):
    """
    Settings adapter - delegates to config loaders from config/

    BACKWARD COMPATIBILITY: This class is maintained for existing code (34+ files).
    New code should use: from config import models, features, app, rag

    Example (old):
        settings = get_settings()
        db_url = settings.DATABASE_URL

    Example (new):
        from config import app
        db_url = app.database.url

    Architecture:
    - Properties delegate to config loaders (config.app, config.features, etc.)
    - Environment variables override YAML values
    - Lazy imports in __init__ to avoid circular dependencies
    - Deprecation warnings for LLM/RAG/Features (not for infrastructure)
    """

    def __init__(self, **kwargs):
        """Initialize settings by loading from config/ directory."""
        super().__init__(**kwargs)

        # Lazy import to avoid circular dependencies
        from config import models, features, app, rag, demographics

        self._config_models = models
        self._config_features = features
        self._config_app = app
        self._config_rag = rag
        self._config_demographics = demographics

    # ═══════════════════════════════════════════════════════════════════════════
    # DATABASE (PostgreSQL)
    # ═══════════════════════════════════════════════════════════════════════════

    @property
    def DATABASE_URL(self) -> str:
        """
        Database connection URL (PostgreSQL + asyncpg).

        Returns:
            str: Connection string z env override
        """
        return os.getenv(
            "DATABASE_URL",
            self._config_app.database.url
        )

    @property
    def POSTGRES_USER(self) -> str:
        """
        Postgres username.

        Returns:
            str: Username z env override
        """
        return os.getenv(
            "POSTGRES_USER",
            self._config_app.database.user or "sight"
        )

    @property
    def POSTGRES_PASSWORD(self) -> str:
        """
        Postgres password.

        Returns:
            str: Password z env override
        """
        return os.getenv(
            "POSTGRES_PASSWORD",
            self._config_app.database.password or "password"
        )

    @property
    def POSTGRES_DB(self) -> str:
        """
        Postgres database name.

        Returns:
            str: Database name z env override
        """
        return os.getenv(
            "POSTGRES_DB",
            self._config_app.database.db_name or "sight_db"
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # REDIS (Cache)
    # ═══════════════════════════════════════════════════════════════════════════

    @property
    def REDIS_URL(self) -> str:
        """
        Redis connection URL.

        Returns:
            str: Connection string z env override
        """
        return os.getenv(
            "REDIS_URL",
            self._config_app.redis.url
        )

    @property
    def REDIS_MAX_CONNECTIONS(self) -> int:
        """
        Redis max connections pool size.

        Returns:
            int: Max connections
        """
        return self._config_app.redis.max_connections

    @property
    def REDIS_SOCKET_TIMEOUT(self) -> int:
        """
        Redis socket timeout (seconds).

        Returns:
            int: Timeout in seconds
        """
        return self._config_app.redis.socket_timeout

    @property
    def REDIS_SOCKET_KEEPALIVE(self) -> bool:
        """
        Redis socket keepalive (zapobiega connection closed errors).

        Returns:
            bool: Keepalive enabled
        """
        return self._config_app.redis.socket_keepalive

    @property
    def REDIS_HEALTH_CHECK_INTERVAL(self) -> int:
        """
        Redis health check interval (seconds).

        Returns:
            int: Interval in seconds
        """
        return self._config_app.redis.health_check_interval

    @property
    def REDIS_RETRY_ON_TIMEOUT(self) -> bool:
        """
        Redis retry on timeout (automatyczny retry przy timeout errors).

        Returns:
            bool: Retry enabled
        """
        return self._config_app.redis.retry_on_timeout

    @property
    def REDIS_MAX_RETRIES(self) -> int:
        """
        Redis max retry attempts dla transient failures.

        Returns:
            int: Max retries
        """
        return self._config_app.redis.max_retries

    @property
    def REDIS_RETRY_BACKOFF(self) -> float:
        """
        Redis retry backoff (seconds) - czekaj przed retry.

        Returns:
            float: Backoff in seconds
        """
        return self._config_app.redis.retry_backoff

    # ═══════════════════════════════════════════════════════════════════════════
    # CELERY (Task Queue - Optional)
    # ═══════════════════════════════════════════════════════════════════════════

    @property
    def CELERY_BROKER_URL(self) -> str | None:
        """
        Celery broker URL (opcjonalne).

        Returns:
            str | None: Broker URL z env override
        """
        return os.getenv(
            "CELERY_BROKER_URL",
            self._config_app.celery.broker_url
        )

    @property
    def CELERY_RESULT_BACKEND(self) -> str | None:
        """
        Celery result backend URL (opcjonalne).

        Returns:
            str | None: Result backend URL z env override
        """
        return os.getenv(
            "CELERY_RESULT_BACKEND",
            self._config_app.celery.result_backend
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # NEO4J (Graph Database)
    # ═══════════════════════════════════════════════════════════════════════════

    @property
    def NEO4J_URI(self) -> str:
        """
        Neo4j connection URI (bolt://...).

        Returns:
            str: Connection URI z env override
        """
        return os.getenv(
            "NEO4J_URI",
            self._config_app.neo4j.uri
        )

    @property
    def NEO4J_USER(self) -> str:
        """
        Neo4j username.

        Returns:
            str: Username z env override
        """
        return os.getenv(
            "NEO4J_USER",
            self._config_app.neo4j.user
        )

    @property
    def NEO4J_PASSWORD(self) -> str:
        """
        Neo4j password.

        Returns:
            str: Password z env override
        """
        return os.getenv(
            "NEO4J_PASSWORD",
            self._config_app.neo4j.password
        )

    @property
    def NEO4J_MAX_POOL_SIZE(self) -> int:
        """
        Neo4j max connections per Cloud Run instance.

        Returns:
            int: Max pool size
        """
        return self._config_app.neo4j.max_pool_size

    @property
    def NEO4J_CONNECTION_TIMEOUT(self) -> int:
        """
        Neo4j TCP connection timeout (seconds).

        Returns:
            int: Timeout in seconds
        """
        return self._config_app.neo4j.connection_timeout

    @property
    def NEO4J_MAX_RETRY_TIME(self) -> int:
        """
        Neo4j max time to retry transient failures (seconds).

        Returns:
            int: Max retry time in seconds
        """
        return self._config_app.neo4j.max_retry_time

    # ═══════════════════════════════════════════════════════════════════════════
    # API KEYS (LLM Providers)
    # ═══════════════════════════════════════════════════════════════════════════

    @property
    def OPENAI_API_KEY(self) -> str | None:
        """
        OpenAI API key (z env: OPENAI_API_KEY).

        Returns:
            str | None: API key or None
        """
        return os.getenv("OPENAI_API_KEY")

    @property
    def ANTHROPIC_API_KEY(self) -> str | None:
        """
        Anthropic API key (z env: ANTHROPIC_API_KEY).

        Returns:
            str | None: API key or None
        """
        return os.getenv("ANTHROPIC_API_KEY")

    @property
    def GOOGLE_API_KEY(self) -> str | None:
        """
        Google API key (z env: GOOGLE_API_KEY).

        Returns:
            str | None: API key or None
        """
        return os.getenv("GOOGLE_API_KEY")

    # ═══════════════════════════════════════════════════════════════════════════
    # SECURITY (JWT, Auth)
    # ═══════════════════════════════════════════════════════════════════════════

    @property
    def SECRET_KEY(self) -> str:
        """
        JWT secret key (ZMIEŃ W PRODUKCJI!).

        Returns:
            str: Secret key z env override
        """
        return os.getenv(
            "SECRET_KEY",
            self._config_app.secret_key
        )

    @property
    def ALGORITHM(self) -> str:
        """
        JWT signing algorithm (domyślnie HS256).

        Returns:
            str: Algorithm name
        """
        return self._config_app.algorithm

    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        """
        JWT token expiration time (minutes).

        Returns:
            int: Expiration time in minutes
        """
        return self._config_app.access_token_expire_minutes

    # ═══════════════════════════════════════════════════════════════════════════
    # LLM MODELS (DEPRECATED - use config.models)
    # ═══════════════════════════════════════════════════════════════════════════

    @property
    def DEFAULT_LLM_PROVIDER(self) -> str:
        """
        DEPRECATED: Use config.models instead.

        Domyślny provider (google, openai, anthropic).

        Returns:
            str: Provider name
        """
        warnings.warn(
            "Settings.DEFAULT_LLM_PROVIDER is deprecated. Use config.models",
            DeprecationWarning,
            stacklevel=2
        )
        # Fallback: zwróć "google" (domyślny provider w models.yaml)
        return "google"

    @property
    def PERSONA_GENERATION_MODEL(self) -> str:
        """
        DEPRECATED: Use config.models.get('personas', 'generation').model

        Model do generowania person (szybki).

        Returns:
            str: Model name (e.g., "gemini-2.0-flash")
        """
        warnings.warn(
            "Settings.PERSONA_GENERATION_MODEL is deprecated. Use config.models",
            DeprecationWarning,
            stacklevel=2
        )
        model_config = self._config_models.get("personas", "generation")
        return model_config.model

    @property
    def ANALYSIS_MODEL(self) -> str:
        """
        DEPRECATED: Use config.models.get('focus_groups', 'summarization').model

        Model do analizy i podsumowań (dokładny).

        Returns:
            str: Model name (e.g., "gemini-2.5-pro")
        """
        warnings.warn(
            "Settings.ANALYSIS_MODEL is deprecated. Use config.models",
            DeprecationWarning,
            stacklevel=2
        )
        model_config = self._config_models.get("focus_groups", "summarization")
        return model_config.model

    @property
    def GRAPH_MODEL(self) -> str:
        """
        DEPRECATED: Use config.models.get('graph', 'creation').model

        Model do tworzenia grafu z raportu.

        Returns:
            str: Model name (e.g., "gemini-2.0-flash")
        """
        warnings.warn(
            "Settings.GRAPH_MODEL is deprecated. Use config.models",
            DeprecationWarning,
            stacklevel=2
        )
        # Fallback: jeśli nie ma 'graph' domain, zwróć gemini-2.0-flash
        try:
            model_config = self._config_models.get("graph", "creation")
            return model_config.model
        except (KeyError, AttributeError):
            return "gemini-2.0-flash"

    @property
    def DEFAULT_MODEL(self) -> str:
        """
        DEPRECATED: Use config.models instead.

        Domyślny model (dla backward compatibility).

        Returns:
            str: Model name
        """
        warnings.warn(
            "Settings.DEFAULT_MODEL is deprecated. Use config.models",
            DeprecationWarning,
            stacklevel=2
        )
        return "gemini-2.0-flash"

    @property
    def TEMPERATURE(self) -> float:
        """
        DEPRECATED: Use config.models.get(domain, service).temperature

        Kreatywność modelu (0.0-1.0).

        Returns:
            float: Temperature value
        """
        warnings.warn(
            "Settings.TEMPERATURE is deprecated. Use config.models (each model has own temperature)",
            DeprecationWarning,
            stacklevel=2
        )
        return 0.7

    @property
    def MAX_TOKENS(self) -> int:
        """
        DEPRECATED: Use config.models.get(domain, service).max_tokens

        Maksymalna długość odpowiedzi.

        Returns:
            int: Max tokens
        """
        warnings.warn(
            "Settings.MAX_TOKENS is deprecated. Use config.models (each model has own max_tokens)",
            DeprecationWarning,
            stacklevel=2
        )
        return 6000

    # ═══════════════════════════════════════════════════════════════════════════
    # PERFORMANCE CONFIG (DEPRECATED - use config.features.performance)
    # ═══════════════════════════════════════════════════════════════════════════

    @property
    def MAX_RESPONSE_TIME_PER_PERSONA(self) -> int:
        """
        DEPRECATED: Use config.features.performance.max_response_time_per_persona

        Maksymalny czas odpowiedzi pojedynczej persony (sekundy).

        Returns:
            int: Max response time in seconds
        """
        warnings.warn(
            "Settings.MAX_RESPONSE_TIME_PER_PERSONA is deprecated. Use config.features.performance",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_features.performance.max_response_time_per_persona

    @property
    def MAX_FOCUS_GROUP_TIME(self) -> int:
        """
        DEPRECATED: Use config.features.performance.max_focus_group_time

        Maksymalny całkowity czas wykonania grupy fokusowej (sekundy).

        Returns:
            int: Max focus group time in seconds
        """
        warnings.warn(
            "Settings.MAX_FOCUS_GROUP_TIME is deprecated. Use config.features.performance",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_features.performance.max_focus_group_time

    @property
    def CONSISTENCY_ERROR_THRESHOLD(self) -> float:
        """
        DEPRECATED: Use config.features.performance.consistency_error_threshold

        Próg błędu spójności (0.0-1.0).

        Returns:
            float: Threshold value
        """
        warnings.warn(
            "Settings.CONSISTENCY_ERROR_THRESHOLD is deprecated. Use config.features.performance",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_features.performance.consistency_error_threshold

    @property
    def STATISTICAL_SIGNIFICANCE_THRESHOLD(self) -> float:
        """
        DEPRECATED: Use config.features.performance.statistical_significance_threshold

        Próg istotności statystycznej (p-value).

        Returns:
            float: P-value threshold
        """
        warnings.warn(
            "Settings.STATISTICAL_SIGNIFICANCE_THRESHOLD is deprecated. Use config.features.performance",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_features.performance.statistical_significance_threshold

    @property
    def RANDOM_SEED(self) -> int:
        """
        DEPRECATED: Use config.features.performance.random_seed

        Seed dla reproducibility (ten sam seed = te same wyniki).

        Returns:
            int: Random seed
        """
        warnings.warn(
            "Settings.RANDOM_SEED is deprecated. Use config.features.performance",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_features.performance.random_seed or 42

    # ═══════════════════════════════════════════════════════════════════════════
    # RAG SYSTEM (DEPRECATED - use config.rag)
    # ═══════════════════════════════════════════════════════════════════════════

    @property
    def RAG_ENABLED(self) -> bool:
        """
        DEPRECATED: Use config.features.rag.enabled

        Globalny toggle dla systemu RAG.

        Returns:
            bool: RAG enabled
        """
        warnings.warn(
            "Settings.RAG_ENABLED is deprecated. Use config.features.rag.enabled",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_features.rag.enabled

    @property
    def RAG_CHUNK_SIZE(self) -> int:
        """
        DEPRECATED: Use config.rag.chunking.chunk_size

        Rozmiar chunków tekstowych (znaki).

        Returns:
            int: Chunk size
        """
        warnings.warn(
            "Settings.RAG_CHUNK_SIZE is deprecated. Use config.rag.chunking.chunk_size",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_rag.chunking.chunk_size

    @property
    def RAG_CHUNK_OVERLAP(self) -> int:
        """
        DEPRECATED: Use config.rag.chunking.chunk_overlap

        Overlap między chunkami (znaki).

        Returns:
            int: Chunk overlap
        """
        warnings.warn(
            "Settings.RAG_CHUNK_OVERLAP is deprecated. Use config.rag.chunking.chunk_overlap",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_rag.chunking.chunk_overlap

    @property
    def RAG_TOP_K(self) -> int:
        """
        DEPRECATED: Use config.rag.retrieval.top_k

        Liczba top wyników z retrieval.

        Returns:
            int: Top K results
        """
        warnings.warn(
            "Settings.RAG_TOP_K is deprecated. Use config.rag.retrieval.top_k",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_rag.retrieval.top_k

    @property
    def RAG_MAX_CONTEXT_CHARS(self) -> int:
        """
        DEPRECATED: Use config.rag.retrieval.max_context_chars

        Maksymalna długość kontekstu RAG (znaki).

        Returns:
            int: Max context chars
        """
        warnings.warn(
            "Settings.RAG_MAX_CONTEXT_CHARS is deprecated. Use config.rag.retrieval.max_context_chars",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_rag.retrieval.max_context_chars

    @property
    def DOCUMENT_STORAGE_PATH(self) -> str:
        """
        Ścieżka do katalogu z dokumentami.

        Returns:
            str: Document storage path
        """
        return self._config_app.document_storage.path

    @property
    def MAX_DOCUMENT_SIZE_MB(self) -> int:
        """
        Maksymalny rozmiar uploadowanego dokumentu (MB).

        Returns:
            int: Max document size in MB
        """
        return self._config_app.document_storage.max_size_mb

    @property
    def RAG_USE_HYBRID_SEARCH(self) -> bool:
        """
        DEPRECATED: Use config.rag.retrieval.use_hybrid_search

        Hybrid search: czy używać keyword search + vector search.

        Returns:
            bool: Hybrid search enabled
        """
        warnings.warn(
            "Settings.RAG_USE_HYBRID_SEARCH is deprecated. Use config.rag.retrieval.use_hybrid_search",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_rag.retrieval.use_hybrid_search

    @property
    def RAG_VECTOR_WEIGHT(self) -> float:
        """
        DEPRECATED: Use config.rag.retrieval.vector_weight

        Hybrid search: waga vector search (0.0-1.0).

        Returns:
            float: Vector weight
        """
        warnings.warn(
            "Settings.RAG_VECTOR_WEIGHT is deprecated. Use config.rag.retrieval.vector_weight",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_rag.retrieval.vector_weight

    @property
    def RAG_RRF_K(self) -> int:
        """
        DEPRECATED: Use config.rag.retrieval.rrf_k

        RRF k parameter (wygładzanie rangi w Reciprocal Rank Fusion).

        Returns:
            int: RRF k parameter
        """
        warnings.warn(
            "Settings.RAG_RRF_K is deprecated. Use config.rag.retrieval.rrf_k",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_rag.retrieval.rrf_k

    @property
    def RAG_USE_RERANKING(self) -> bool:
        """
        DEPRECATED: Use config.rag.retrieval.use_reranking

        Reranking: włącz cross-encoder dla precyzyjniejszego scoringu.

        Returns:
            bool: Reranking enabled
        """
        warnings.warn(
            "Settings.RAG_USE_RERANKING is deprecated. Use config.rag.retrieval.use_reranking",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_rag.retrieval.use_reranking

    @property
    def RAG_RERANK_CANDIDATES(self) -> int:
        """
        DEPRECATED: Use config.rag.retrieval.rerank_candidates

        Liczba candidatów dla reranking (przed finalnym top_k).

        Returns:
            int: Rerank candidates count
        """
        warnings.warn(
            "Settings.RAG_RERANK_CANDIDATES is deprecated. Use config.rag.retrieval.rerank_candidates",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_rag.retrieval.rerank_candidates

    @property
    def RAG_RERANKER_MODEL(self) -> str:
        """
        DEPRECATED: Use config.rag.retrieval.reranker_model

        Cross-encoder model dla reranking.

        Returns:
            str: Reranker model name
        """
        warnings.warn(
            "Settings.RAG_RERANKER_MODEL is deprecated. Use config.rag.retrieval.reranker_model",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_rag.retrieval.reranker_model

    # ═══════════════════════════════════════════════════════════════════════════
    # GRAPH RAG NODE PROPERTIES (DEPRECATED - use config.features.rag)
    # ═══════════════════════════════════════════════════════════════════════════

    @property
    def RAG_NODE_PROPERTIES_ENABLED(self) -> bool:
        """
        DEPRECATED: Use config.features.rag.node_properties_enabled

        Włączanie bogatych metadanych węzłów.

        Returns:
            bool: Node properties enabled
        """
        warnings.warn(
            "Settings.RAG_NODE_PROPERTIES_ENABLED is deprecated. Use config.features.rag.node_properties_enabled",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_features.rag.node_properties_enabled

    @property
    def RAG_EXTRACT_SUMMARIES(self) -> bool:
        """
        DEPRECATED: Use config.features.rag.extract_summaries

        Ekstrakcja summary dla każdego węzła.

        Returns:
            bool: Extract summaries enabled
        """
        warnings.warn(
            "Settings.RAG_EXTRACT_SUMMARIES is deprecated. Use config.features.rag.extract_summaries",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_features.rag.extract_summaries

    @property
    def RAG_EXTRACT_KEY_FACTS(self) -> bool:
        """
        DEPRECATED: Use config.features.rag.extract_key_facts

        Ekstrakcja key_facts dla węzłów.

        Returns:
            bool: Extract key facts enabled
        """
        warnings.warn(
            "Settings.RAG_EXTRACT_KEY_FACTS is deprecated. Use config.features.rag.extract_key_facts",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_features.rag.extract_key_facts

    @property
    def RAG_RELATIONSHIP_CONFIDENCE(self) -> bool:
        """
        DEPRECATED: Use config.features.rag.relationship_confidence

        Ekstrakcja confidence dla relacji.

        Returns:
            bool: Relationship confidence enabled
        """
        warnings.warn(
            "Settings.RAG_RELATIONSHIP_CONFIDENCE is deprecated. Use config.features.rag.relationship_confidence",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_features.rag.relationship_confidence

    # ═══════════════════════════════════════════════════════════════════════════
    # ORCHESTRATION (DEPRECATED - use config.features.orchestration)
    # ═══════════════════════════════════════════════════════════════════════════

    @property
    def ORCHESTRATION_ENABLED(self) -> bool:
        """
        DEPRECATED: Use config.features.orchestration.enabled

        Feature flag: Enable persona orchestration with Gemini 2.5 Pro.

        Returns:
            bool: Orchestration enabled
        """
        warnings.warn(
            "Settings.ORCHESTRATION_ENABLED is deprecated. Use config.features.orchestration.enabled",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_features.orchestration.enabled

    @property
    def ORCHESTRATION_TIMEOUT(self) -> int:
        """
        DEPRECATED: Use config.features.orchestration.timeout

        Orchestration timeout (seconds).

        Returns:
            int: Timeout in seconds
        """
        warnings.warn(
            "Settings.ORCHESTRATION_TIMEOUT is deprecated. Use config.features.orchestration.timeout",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_features.orchestration.timeout

    # ═══════════════════════════════════════════════════════════════════════════
    # EMBEDDINGS (DEPRECATED - use config.models)
    # ═══════════════════════════════════════════════════════════════════════════

    @property
    def EMBEDDING_MODEL(self) -> str:
        """
        DEPRECATED: Use config.models.get('embeddings', 'default').model

        Model do generowania embeddingów tekstowych.

        Returns:
            str: Embedding model name
        """
        warnings.warn(
            "Settings.EMBEDDING_MODEL is deprecated. Use config.models",
            DeprecationWarning,
            stacklevel=2
        )
        # Fallback: zwróć gemini-embedding-001
        try:
            model_config = self._config_models.get("embeddings", "default")
            return model_config.model
        except (KeyError, AttributeError):
            return "gemini-embedding-001"

    @property
    def EMBEDDING_DIMENSION(self) -> int:
        """
        DEPRECATED: Use config.models.get('embeddings', 'default').dimension

        Wymiarowość wektorów embeddingowych.

        Returns:
            int: Embedding dimension
        """
        warnings.warn(
            "Settings.EMBEDDING_DIMENSION is deprecated. Use config.models",
            DeprecationWarning,
            stacklevel=2
        )
        # gemini-embedding-001 generuje 3072-wymiarowe wektory
        return 3072

    # ═══════════════════════════════════════════════════════════════════════════
    # SEGMENT CACHE (DEPRECATED - use config.features.segment_cache)
    # ═══════════════════════════════════════════════════════════════════════════

    @property
    def SEGMENT_CACHE_ENABLED(self) -> bool:
        """
        DEPRECATED: Use config.features.segment_cache.enabled

        Feature flag: Włącz segment-first cache (zamiast per-persona RAG).

        Returns:
            bool: Segment cache enabled
        """
        warnings.warn(
            "Settings.SEGMENT_CACHE_ENABLED is deprecated. Use config.features.segment_cache.enabled",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_features.segment_cache.enabled

    @property
    def SEGMENT_CACHE_TTL_DAYS(self) -> int:
        """
        DEPRECATED: Use config.features.segment_cache.ttl_days

        TTL dla segment cache w Redis (dni).

        Returns:
            int: TTL in days
        """
        warnings.warn(
            "Settings.SEGMENT_CACHE_TTL_DAYS is deprecated. Use config.features.segment_cache.ttl_days",
            DeprecationWarning,
            stacklevel=2
        )
        return self._config_features.segment_cache.ttl_days

    @property
    def RETRIEVAL_MODE(self) -> str:
        """
        DEPRECATED: Use config.rag.retrieval.mode

        Retrieval mode dla RetrievalService (vector / hybrid / hybrid+rerank).

        Returns:
            str: Retrieval mode
        """
        warnings.warn(
            "Settings.RETRIEVAL_MODE is deprecated. Use config.rag.retrieval.mode",
            DeprecationWarning,
            stacklevel=2
        )
        # Fallback: zwróć "vector" (domyślny mode)
        return getattr(self._config_rag.retrieval, 'mode', 'vector')

    @property
    def RERANK_THRESHOLD(self) -> int:
        """
        DEPRECATED: Use config.rag.retrieval.rerank_threshold

        Threshold dla auto-switching do hybrid search.

        Returns:
            int: Rerank threshold
        """
        warnings.warn(
            "Settings.RERANK_THRESHOLD is deprecated. Use config.rag.retrieval.rerank_threshold",
            DeprecationWarning,
            stacklevel=2
        )
        # Fallback: zwróć 3
        return getattr(self._config_rag.retrieval, 'rerank_threshold', 3)

    # ═══════════════════════════════════════════════════════════════════════════
    # ENVIRONMENT (App Settings)
    # ═══════════════════════════════════════════════════════════════════════════

    @property
    def ENVIRONMENT(self) -> str:
        """
        Current environment (development / staging / production).

        Returns:
            str: Environment name
        """
        return os.getenv("ENVIRONMENT", self._config_app.environment)

    @property
    def DEBUG(self) -> bool:
        """
        Debug mode (włącz szczegółowe logi błędów).

        Returns:
            bool: Debug enabled
        """
        debug_env = os.getenv("DEBUG")
        if debug_env is not None:
            return debug_env.lower() in ("true", "1", "yes")
        return self._config_app.debug

    @property
    def LOG_LEVEL(self) -> str:
        """
        Log level (CRITICAL, ERROR, WARNING, INFO, DEBUG).

        Returns:
            str: Log level
        """
        return os.getenv("LOG_LEVEL", "DEBUG" if self.DEBUG else "INFO")

    @property
    def STRUCTURED_LOGGING(self) -> bool:
        """
        Structured logging (JSON format dla Cloud Logging).

        Returns:
            bool: Structured logging enabled
        """
        structured_env = os.getenv("STRUCTURED_LOGGING")
        if structured_env is not None:
            return structured_env.lower() in ("true", "1", "yes")
        # Auto-enable for production
        return self.ENVIRONMENT == "production"

    @property
    def structured_logging_enabled(self) -> bool:
        """
        Determine whether to use structured JSON logging.

        Auto-enable for production, manual override with STRUCTURED_LOGGING env var.

        Returns:
            bool: Structured logging enabled
        """
        # Explicitly set by env var - respect it
        structured_env = os.getenv("STRUCTURED_LOGGING")
        if structured_env is not None:
            return structured_env.lower() in ("true", "1", "yes")

        # Auto-enable for production
        return self.ENVIRONMENT == "production"

    # ═══════════════════════════════════════════════════════════════════════════
    # API (App Settings)
    # ═══════════════════════════════════════════════════════════════════════════

    @property
    def API_V1_PREFIX(self) -> str:
        """
        Prefix dla wszystkich endpointów API v1.

        Returns:
            str: API prefix (e.g., "/api/v1")
        """
        return self._config_app.api_prefix

    @property
    def PROJECT_NAME(self) -> str:
        """
        Nazwa projektu (wyświetlana w docs).

        Returns:
            str: Project name
        """
        return self._config_app.project_name

    @property
    def ALLOWED_ORIGINS(self) -> str:
        """
        Lista origin dozwolonych dla CORS (rozdzielone przecinkami).

        Returns:
            str: Comma-separated origins
        """
        # Convert list to comma-separated string (backward compatibility)
        return ",".join(self._config_app.allowed_origins)

    class Config:
        env_file = ".env"
        case_sensitive = True
        # Allow env vars that don't match properties (they're accessed via properties)
        extra = "ignore"  # Pydantic v2: ignore extra fields from env


@lru_cache()
def get_settings() -> Settings:
    """
    Pobierz instancję ustawień (cache'owana).

    BACKWARD COMPATIBILITY: Function preserved for existing code (34+ files).
    New code should use: from config import models, features, app

    Używa @lru_cache() żeby stworzyć tylko jedną instancję Settings
    dla całej aplikacji (singleton pattern). To zapewnia że wszystkie
    części aplikacji używają tych samych ustawień.

    Returns:
        Settings: Obiekt z wszystkimi ustawieniami aplikacji
    """
    return Settings()
