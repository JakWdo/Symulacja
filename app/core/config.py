"""
Konfiguracja aplikacji

Moduł dostarcza klasę `Settings`, która zbiera wszystkie
zmienne środowiskowe projektu (baza danych, LLM-y, bezpieczeństwo).
Funkcja `get_settings()` zwraca jedną, współdzieloną instancję ustawień.
"""

from functools import lru_cache

try:
    from pydantic_settings import BaseSettings
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    from pydantic import BaseSettings  # type: ignore


class Settings(BaseSettings):
    """
    Ustawienia aplikacji z wsparciem dla zmiennych środowiskowych

    Wszystkie wartości mogą być nadpisane przez zmienne środowiskowe z pliku .env
    lub zmienne systemowe. Nazwy zmiennych są case-sensitive.
    """

    # === BAZA DANYCH ===
    # PostgreSQL z asyncpg driver (wymagane dla SQLAlchemy async)
    DATABASE_URL: str = "postgresql+asyncpg://sight:password@localhost:5432/sight_db"
    POSTGRES_USER: str = "sight"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "sight_db"

    # === CACHE ===
    # Redis do cache'owania
    # WAŻNE: Dla Upstash Redis w produkcji użyj rediss:// (z SSL/TLS)
    # Development: redis://localhost:6379/0
    # Production: rediss://default:TOKEN@HOST:6379 (z TLS!)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Redis Connection Pool Settings (Upstash optimization)
    # Maksymalna liczba połączeń w pool (Cloud Run może mieć wiele workers)
    REDIS_MAX_CONNECTIONS: int = 50
    # Socket timeout (sekundy) - timeout dla pojedynczej operacji Redis
    # Upstash może mieć wyższą latency (~50-100ms), więc 5s to bezpieczny margin
    REDIS_SOCKET_TIMEOUT: int = 5
    # Socket keepalive - utrzymuj połączenia alive między requestami
    # KLUCZOWE dla Upstash: zapobiega "Connection closed by server" errors
    REDIS_SOCKET_KEEPALIVE: bool = True
    # Health check interval (sekundy) - ping Redis co N sekund
    # Upstash może timeout'ować idle connections (~60s), więc 30s to safe guard
    REDIS_HEALTH_CHECK_INTERVAL: int = 30
    # Retry on timeout - automatyczny retry przy timeout errors
    REDIS_RETRY_ON_TIMEOUT: bool = True
    # Max retry attempts dla transient failures (connection errors, timeouts)
    REDIS_MAX_RETRIES: int = 3
    # Retry backoff (sekundy) - czekaj N sekund przed retry
    REDIS_RETRY_BACKOFF: float = 0.5

    # === TASK QUEUE (opcjonalnie) ===
    # Umożliwia ustawienie broker backend dla Celery bez wymuszania ich obecności
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    # === GRAF WIEDZY ===
    # Neo4j używany dla graph analysis i RAG vectorstore
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # Neo4j Connection Pool Settings (Cloud Run optimization)
    # Prevent connection exhaustion and improve reliability in production
    NEO4J_MAX_POOL_SIZE: int = 50  # Max connections per Cloud Run instance
    NEO4J_CONNECTION_TIMEOUT: int = 30  # TCP connection timeout (seconds)
    NEO4J_MAX_RETRY_TIME: int = 30  # Max time to retry transient failures

    # === KLUCZE API LLM ===
    # Klucze do modeli językowych (jeden musi być ustawiony)
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None  # Używany domyślnie (Gemini)

    # === BEZPIECZEŃSTWO ===
    # SECRET_KEY: Używany do podpisywania tokenów JWT (ZMIEŃ W PRODUKCJI!)
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"  # Algorytm podpisywania JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Czas wygaśnięcia tokenów

    # === MODELE LLM ===
    # DEFAULT_LLM_PROVIDER: Domyślny provider (google, openai, anthropic)
    DEFAULT_LLM_PROVIDER: str = "google"
    # PERSONA_GENERATION_MODEL: Model do generowania person (szybki)
    PERSONA_GENERATION_MODEL: str = "gemini-2.5-flash"
    # ANALYSIS_MODEL: Model do analizy i podsumowań (dokładny)
    ANALYSIS_MODEL: str = "gemini-2.5-pro"
    # GRAPH_MODEL: Model do tworzenia grafu z raportu
    GRAPH_MODEL: str = "gemini-2.5-flash"
    # DEFAULT_MODEL: ustawienie utrzymujące zgodność wsteczną
    DEFAULT_MODEL: str = "gemini-2.5-flash"
    # TEMPERATURE: Kreatywność modelu (0.0-1.0, wyższe = bardziej kreatywne)
    TEMPERATURE: float = 0.7
    # MAX_TOKENS: Maksymalna długość odpowiedzi
    MAX_TOKENS: int = 6000

    # === CELE WYDAJNOŚCIOWE ===
    # Maksymalny czas odpowiedzi pojedynczej persony (sekundy)
    MAX_RESPONSE_TIME_PER_PERSONA: int = 3
    # Maksymalny całkowity czas wykonania grupy fokusowej (sekundy)
    MAX_FOCUS_GROUP_TIME: int = 30
    # Próg błędu spójności (0.0-1.0)
    CONSISTENCY_ERROR_THRESHOLD: float = 0.05
    # Próg istotności statystycznej (p-value, domyślnie 0.05)
    STATISTICAL_SIGNIFICANCE_THRESHOLD: float = 0.05
    # Seed dla reproducibility (ten sam seed = te same wyniki)
    RANDOM_SEED: int = 42

    # === RAG SYSTEM (Retrieval-Augmented Generation) ===
    # Globalny toggle dla systemu RAG
    RAG_ENABLED: bool = True
    # Rozmiar chunków tekstowych (znaki)
    # Mniejsze chunki dają lepszą precyzję embeddings - jeden embedding reprezentuje bardziej focused kontekst
    RAG_CHUNK_SIZE: int = 1000
    # Overlap między chunkami (znaki)
    # 30% overlap zapobiega rozdzielaniu ważnych informacji między chunkami
    RAG_CHUNK_OVERLAP: int = 300
    # Liczba top wyników z retrieval
    # Więcej results kompensuje mniejszy rozmiar chunków, zachowując podobną ilość kontekstu
    RAG_TOP_K: int = 8
    # Maksymalna długość kontekstu RAG (znaki)
    # OPTIMIZATION: Reduced from 12000 → 8000 to reduce LLM input tokens
    # Still sufficient for TOP_K=8 chunks (8 × 1000 = 8000) + moderate graph context
    RAG_MAX_CONTEXT_CHARS: int = 8000
    # Ścieżka do katalogu z dokumentami
    DOCUMENT_STORAGE_PATH: str = "data/documents"
    # Maksymalny rozmiar uploadowanego dokumentu (50MB)
    MAX_DOCUMENT_SIZE_MB: int = 50
    # Hybrid search: czy używać keyword search + vector search
    RAG_USE_HYBRID_SEARCH: bool = True
    # Hybrid search: waga vector search (0.0-1.0, reszta to keyword)
    RAG_VECTOR_WEIGHT: float = 0.7
    # RRF k parameter (wygładzanie rangi w Reciprocal Rank Fusion)
    # Niższe k (40) favoryzuje top results, wyższe k (80) traktuje równomiernie
    # k=60 to sprawdzony balans - eksperymentuj używając test_rrf_k_tuning.py
    RAG_RRF_K: int = 60
    # Reranking: włącz cross-encoder dla precyzyjniejszego scoringu query-document pairs
    RAG_USE_RERANKING: bool = True
    # Liczba candidatów dla reranking (przed finalnym top_k)
    # OPTIMIZATION (2025-10-28): Adaptive tuning dla production Cloud Run
    # - 10 candidates = 1.0-1.5s @ 1 CPU (Cloud Run default)
    # - 5 candidates = ~500ms @ 1 CPU (low-latency mode)
    # - async offload (asyncio.to_thread) = non-blocking, parallel requests OK
    RAG_RERANK_CANDIDATES: int = 10
    # Cross-encoder model dla reranking
    # FIX: Poprzedni model "mmarco-mMiniLMv2-L6-v1" nie istniał na HuggingFace
    # CURRENT: ms-marco-MiniLM-L-6-v2 - English, 6 layers, SZYBKI (~100-150ms per doc)
    # ALTERNATIVE: "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1" (multilingual, wolniejszy)
    # PRODUCTION NOTE: Model pre-warmed in Dockerfile (eliminates 3-5s cold start)
    RAG_RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # === GraphRAG NODE PROPERTIES ===
    # Włączanie bogatych metadanych węzłów
    RAG_NODE_PROPERTIES_ENABLED: bool = True
    # Ekstrakcja summary dla każdego węzła
    RAG_EXTRACT_SUMMARIES: bool = True
    # Ekstrakcja key_facts dla węzłów
    RAG_EXTRACT_KEY_FACTS: bool = True
    # Ekstrakcja confidence dla relacji
    RAG_RELATIONSHIP_CONFIDENCE: bool = True

    # === ORCHESTRATION SERVICE (Persona Generation) ===
    # Feature flag: Enable persona orchestration with Gemini 2.5 Pro
    # Benefits:
    #   - Długie briefe (900-1200 chars) dla każdego demographic group
    #   - Graph RAG insights (3-5 insights per group)
    #   - Segment characteristics (4-6 kluczowych cech)
    #   - Allocation reasoning (dlaczego tyle person w grupie)
    # Trade-off: ~10-20s latency z cachingiem (vs 2-5s basic generation)
    # Rollback: Ustaw na False aby wrócić do basic generation (bez detailed reasoning)
    ORCHESTRATION_ENABLED: bool = True

    # Orchestration timeout (seconds)
    # With Redis caching + optimized queries: should complete in 10-20s
    # Without caching (cold start): may take up to 60s
    ORCHESTRATION_TIMEOUT: int = 90  # Safety margin for Cloud Run

    # === EMBEDDINGS (Google Gemini) ===
    # Model do generowania embeddingów tekstowych
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    # Wymiarowość wektorów embeddingowych
    # gemini-embedding-001 generuje 3072-wymiarowe wektory (nie 768!)
    EMBEDDING_DIMENSION: int = 3072

    # === SEGMENT CACHE (Faza 2 - Segment-First Architecture) ===
    # Feature flag: Włącz segment-first cache (zamiast per-persona RAG)
    # Benefits: 3x szybsze, 60% mniej tokenów, lepsza spójność
    # Rollback: Ustaw na False aby wrócić do starego flow
    SEGMENT_CACHE_ENABLED: bool = True
    # TTL dla segment cache w Redis (dni)
    SEGMENT_CACHE_TTL_DAYS: int = 7
    # Retrieval mode dla RetrievalService
    # - "vector": Tylko vector search (najszybsze, ~500ms)
    # - "hybrid": Vector + keyword + RRF (~1000ms)
    # - "hybrid+rerank": + cross-encoder reranking (~1500ms)
    RETRIEVAL_MODE: str = "vector"
    # Threshold dla auto-switching do hybrid search
    # Jeśli vector results < N, przełącz na hybrid (quality safeguard)
    RERANK_THRESHOLD: int = 3

    # === ŚRODOWISKO ===
    # ENVIRONMENT: development / staging / production
    ENVIRONMENT: str = "development"
    # DEBUG: Włącz szczegółowe logi błędów
    DEBUG: bool = True
    # LOG_LEVEL: Poziom logowania (CRITICAL, ERROR, WARNING, INFO, DEBUG)
    # Production: INFO (strukturalne logi bez debug noise)
    # Development: DEBUG (szczegółowe logi dla debugging)
    LOG_LEVEL: str = "DEBUG"
    # STRUCTURED_LOGGING: JSON format dla Cloud Logging (production)
    # CRITICAL FIX: Automatycznie włącz structured logging w production
    # True w production umożliwia łatwe filtrowanie w GCP Logs Explorer
    # Development: False (human-readable logs), Production: True (JSON)
    STRUCTURED_LOGGING: bool = False

    @property
    def structured_logging_enabled(self) -> bool:
        """
        Determine whether to use structured JSON logging

        Auto-enable for production, manual override with STRUCTURED_LOGGING env var
        """
        # Explicitly set by env var - respect it
        import os

        if os.getenv("STRUCTURED_LOGGING") is not None:
            return self.STRUCTURED_LOGGING

        # Auto-enable for production
        return self.ENVIRONMENT == "production"

    # === API ===
    # Prefix dla wszystkich endpointów API v1
    API_V1_PREFIX: str = "/api/v1"
    # Nazwa projektu (wyświetlana w docs)
    PROJECT_NAME: str = "Sight"
    # ALLOWED_ORIGINS: Lista origin dozwolonych dla CORS (rozdzielone przecinkami)
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Pobierz instancję ustawień (cache'owana)

    Używa @lru_cache() żeby stworzyć tylko jedną instancję Settings
    dla całej aplikacji (singleton pattern). To zapewnia że wszystkie
    części aplikacji używają tych samych ustawień.

    Returns:
        Settings: Obiekt z wszystkimi ustawieniami aplikacji
    """
    return Settings()
