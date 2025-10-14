"""
Konfiguracja aplikacji

Moduł dostarcza klasę `Settings`, która zbiera wszystkie
zmienne środowiskowe projektu (baza danych, LLM-y, bezpieczeństwo).
Funkcja `get_settings()` zwraca jedną, współdzieloną instancję ustawień.
"""

from typing import Optional
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
    DATABASE_URL: str = "postgresql+asyncpg://market_research:password@localhost:5432/market_research_db"
    POSTGRES_USER: str = "market_research"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "market_research_db"

    # === CACHE I KOLEJKI ===
    # Redis do cache'owania i Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # === GRAF WIEDZY ===
    # Neo4j używany dla graph analysis i RAG vectorstore
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # === KLUCZE API LLM ===
    # Klucze do modeli językowych (jeden musi być ustawiony)
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None  # Używany domyślnie (Gemini)

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
    # DEFAULT_MODEL: ustawienie utrzymujące zgodność wsteczną
    DEFAULT_MODEL: str = "gemini-2.5-flash"
    # TEMPERATURE: Kreatywność modelu (0.0-1.0, wyższe = bardziej kreatywne)
    TEMPERATURE: float = 0.7
    # MAX_TOKENS: Maksymalna długość odpowiedzi
    MAX_TOKENS: int = 8000

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
    # Wystarczająco duży aby pomieścić TOP_K chunków + graph context bez truncation
    RAG_MAX_CONTEXT_CHARS: int = 12000
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
    # Cross-encoder jest wolniejszy, więc rerankujemy więcej niż potrzebujemy i bierzemy top
    RAG_RERANK_CANDIDATES: int = 25
    # Cross-encoder model dla reranking
    # Multilingual model wspiera polski lepiej niż English-only ms-marco-MiniLM
    RAG_RERANKER_MODEL: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

    # === GraphRAG NODE PROPERTIES ===
    # Włączanie bogatych metadanych węzłów
    RAG_NODE_PROPERTIES_ENABLED: bool = True
    # Ekstrakcja summary dla każdego węzła
    RAG_EXTRACT_SUMMARIES: bool = True
    # Ekstrakcja key_facts dla węzłów
    RAG_EXTRACT_KEY_FACTS: bool = True
    # Ekstrakcja confidence dla relacji
    RAG_RELATIONSHIP_CONFIDENCE: bool = True

    # === EMBEDDINGS (Google Gemini) ===
    # Model do generowania embeddingów tekstowych
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    # Wymiarowość wektorów embeddingowych
    # gemini-embedding-001 generuje 3072-wymiarowe wektory (nie 768!)
    EMBEDDING_DIMENSION: int = 3072

    # === CELERY (zadania asynchroniczne) ===
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # === ŚRODOWISKO ===
    # ENVIRONMENT: development / staging / production
    ENVIRONMENT: str = "development"
    # DEBUG: Włącz szczegółowe logi błędów
    DEBUG: bool = True

    # === API ===
    # Prefix dla wszystkich endpointów API v1
    API_V1_PREFIX: str = "/api/v1"
    # Nazwa projektu (wyświetlana w docs)
    PROJECT_NAME: str = "Market Research SaaS"
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
