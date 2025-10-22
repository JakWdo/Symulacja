"""
LLM Model Configuration - Per-service settings

Ten moduł zawiera konfigurację specyficzną dla modeli LLM używanych przez różne serwisy.
Każdy serwis ma własne ustawienia (model, temperature, max_tokens, timeout).

Filozofia:
- Centralna konfiguracja - łatwa modyfikacja bez zmiany kodu serwisów
- Type-safe - walidacja Pydantic
- Environment-aware - można nadpisać przez zmienne środowiskowe
- Production-ready - sensowne defaulty dla każdego use case
"""

from pydantic_settings import BaseSettings
from typing import Optional


class ModelConfig(BaseSettings):
    """
    Konfiguracja modeli LLM dla wszystkich serwisów.

    Każdy serwis ma dedykowane pola z prefiksem:
    - PERSONA_* - PersonaGeneratorLangChain
    - FOCUS_GROUP_* - FocusGroupServiceLangChain
    - SURVEY_* - SurveyResponseGenerator
    - SUMMARIZER_* - DiscussionSummarizerService
    - NEEDS_* - PersonaNeedsService
    - MESSAGING_* - PersonaMessagingService
    - ORCHESTRATION_* - PersonaOrchestrationService
    - GRAPH_* - GraphRAGService, RAGDocumentService

    Przykład użycia:
        from app.core.model_config import get_model_config

        config = get_model_config()
        llm = build_chat_model(
            model=config.PERSONA_MODEL,
            temperature=config.PERSONA_TEMPERATURE,
            max_tokens=config.PERSONA_MAX_TOKENS
        )
    """

    # =========================================================================
    # PERSONA GENERATION - PersonaGeneratorLangChain
    # =========================================================================

    PERSONA_MODEL: str = "gemini-2.5-flash"
    """Model dla generacji person. Flash = szybki, tańszy, wystarczająco dobry."""

    PERSONA_TEMPERATURE: float = 0.9
    """Wysoka temperatura dla większej różnorodności i kreatywności person."""

    PERSONA_MAX_TOKENS: int = 6000
    """Standard max tokens dla person (wystarczy na pełny JSON z background_story)."""

    PERSONA_TOP_P: float = 0.95
    """Top-p sampling dla person - wysoki dla różnorodności."""

    PERSONA_TOP_K: int = 40
    """Top-k sampling dla person - balansuje różnorodność vs jakość."""

    # =========================================================================
    # FOCUS GROUPS - FocusGroupServiceLangChain
    # =========================================================================

    FOCUS_GROUP_MODEL: str = "gemini-2.5-flash"
    """Model dla symulacji focus groups. Flash wystarcza do konwersacyjnych odpowiedzi."""

    FOCUS_GROUP_TEMPERATURE: float = 0.7
    """Standard temperature dla naturalnych, autentycznych odpowiedzi."""

    FOCUS_GROUP_MAX_TOKENS: int = 2048
    """Mniejszy limit dla krótkich odpowiedzi focus group (2-4 zdania)."""

    # =========================================================================
    # SURVEYS - SurveyResponseGenerator
    # =========================================================================

    SURVEY_MODEL: str = "gemini-2.5-flash"
    """Model dla odpowiedzi ankietowych. Flash wystarcza do prostych wyborów."""

    SURVEY_TEMPERATURE: float = 0.7
    """Standard temperature dla realistycznych wyborów."""

    SURVEY_MAX_TOKENS: int = 1024
    """Krótkie odpowiedzi ankietowe - 1024 tokenów wystarczy."""

    # =========================================================================
    # DISCUSSION SUMMARIZER - DiscussionSummarizerService
    # =========================================================================

    SUMMARIZER_MODEL: str = "gemini-2.5-pro"
    """Pro model dla wysokiej jakości analiz i podsumowań."""

    SUMMARIZER_TEMPERATURE: float = 0.3
    """Niska temperatura dla faktycznych, precyzyjnych podsumowań."""

    SUMMARIZER_MAX_TOKENS: int = 4096
    """Długie podsumowania z executive summary, insights, recommendations."""

    # =========================================================================
    # PERSONA NEEDS - PersonaNeedsService (JTBD)
    # =========================================================================

    NEEDS_MODEL: str = "gemini-2.5-pro"
    """Pro model dla głębokiej analizy Jobs-to-be-Done i pain points."""

    NEEDS_TEMPERATURE: float = 0.25
    """Bardzo niska temperatura dla deterministycznej, wysokiej jakości analizy."""

    NEEDS_MAX_TOKENS: int = 4000
    """Wystarczające dla strukturalnego outputu (JTBD + outcomes + pains)."""

    NEEDS_TIMEOUT: int = 120
    """2 minuty timeout dla complex reasoning (JTBD analysis)."""

    # =========================================================================
    # PERSONA MESSAGING - PersonaMessagingService
    # =========================================================================

    MESSAGING_MODEL: str = "gemini-2.5-flash"
    """Flash model dla kreatywnego copy (3 warianty)."""

    MESSAGING_TEMPERATURE: float = 0.7
    """Wysoka temperatura dla kreatywnego marketingowego copy."""

    MESSAGING_MAX_TOKENS: int = 1500
    """Wystarczające dla 3 wariantów (headline + subheadline + body + CTA)."""

    MESSAGING_TIMEOUT: int = 90
    """1.5 minuty timeout dla messaging generation."""

    # =========================================================================
    # ORCHESTRATION - PersonaOrchestrationService
    # =========================================================================

    ORCHESTRATION_MODEL: str = "gemini-2.5-pro"
    """Pro model dla complex reasoning i długich briefów (900-1200 znaków)."""

    ORCHESTRATION_TEMPERATURE: float = 0.3
    """Niska temperatura dla analytical, edukacyjnych briefów."""

    ORCHESTRATION_MAX_TOKENS: int = 8000
    """Długie outputy - plan alokacji + briefe dla każdej grupy."""

    ORCHESTRATION_TIMEOUT: int = 120
    """2 minuty timeout dla complex socjologicznej analizy."""

    # =========================================================================
    # SEGMENT NAMING - PersonaOrchestrationService._generate_segment_name()
    # =========================================================================

    SEGMENT_NAMING_MODEL: str = "gemini-2.0-flash-exp"
    """Flash Exp dla szybkiego generowania nazw segmentów (cheap & fast)."""

    SEGMENT_NAMING_TEMPERATURE: float = 0.7
    """Standard temperature dla kreatywnych nazw segmentów."""

    SEGMENT_NAMING_MAX_TOKENS: int = 50
    """Bardzo krótkie outputy (2-4 słowa nazwy segmentu)."""

    SEGMENT_NAMING_TIMEOUT: int = 10
    """10 sekund timeout dla szybkiego namingu."""

    # =========================================================================
    # GRAPH RAG - GraphRAGService, RAGDocumentService
    # =========================================================================

    GRAPH_MODEL: str = "gemini-2.5-flash"
    """Flash model dla Graph RAG operations (Cypher gen, graph extraction)."""

    GRAPH_TEMPERATURE: float = 0.0
    """Zerowa temperatura dla deterministycznych zapytań Cypher i extrakcji."""

    GRAPH_MAX_TOKENS: int = 6000
    """Standard max tokens dla graph operations."""

    # =========================================================================
    # GENERAL SETTINGS - Shared across services
    # =========================================================================

    DEFAULT_TIMEOUT: int = 60
    """Default timeout dla LLM calls (60 sekund)."""

    RETRY_MAX_ATTEMPTS: int = 3
    """Maksymalna liczba retry attempts dla LLM calls."""

    RETRY_EXPONENTIAL_BACKOFF: bool = True
    """Czy używać exponential backoff dla retries."""

    class Config:
        """Pydantic config - allow overrides from environment variables."""
        env_prefix = "MODEL_"  # MODEL_PERSONA_TEMPERATURE, MODEL_NEEDS_MAX_TOKENS, etc.
        case_sensitive = True


# =========================================================================
# Singleton instance - use this everywhere
# =========================================================================

_model_config_instance: Optional[ModelConfig] = None


def get_model_config() -> ModelConfig:
    """
    Zwraca singleton instance ModelConfig.

    Returns:
        ModelConfig instance z ustawieniami LLM dla wszystkich serwisów

    Przykład:
        >>> config = get_model_config()
        >>> print(config.PERSONA_TEMPERATURE)
        0.9
        >>> print(config.NEEDS_MODEL)
        'gemini-2.5-pro'
    """
    global _model_config_instance
    if _model_config_instance is None:
        _model_config_instance = ModelConfig()
    return _model_config_instance


# =========================================================================
# Helper function - get config for specific service
# =========================================================================

def get_service_llm_config(service_name: str) -> dict:
    """
    Zwraca konfigurację LLM dla konkretnego serwisu.

    Args:
        service_name: Nazwa serwisu (persona, focus_group, survey, etc.)

    Returns:
        Dict z kluczami: model, temperature, max_tokens, timeout

    Przykład:
        >>> config = get_service_llm_config("persona")
        >>> config
        {'model': 'gemini-2.5-flash', 'temperature': 0.9, 'max_tokens': 6000}

    Raises:
        ValueError: Jeśli service_name jest nieznany
    """
    cfg = get_model_config()

    service_configs = {
        "persona": {
            "model": cfg.PERSONA_MODEL,
            "temperature": cfg.PERSONA_TEMPERATURE,
            "max_tokens": cfg.PERSONA_MAX_TOKENS,
            "top_p": cfg.PERSONA_TOP_P,
            "top_k": cfg.PERSONA_TOP_K,
        },
        "focus_group": {
            "model": cfg.FOCUS_GROUP_MODEL,
            "temperature": cfg.FOCUS_GROUP_TEMPERATURE,
            "max_tokens": cfg.FOCUS_GROUP_MAX_TOKENS,
        },
        "survey": {
            "model": cfg.SURVEY_MODEL,
            "temperature": cfg.SURVEY_TEMPERATURE,
            "max_tokens": cfg.SURVEY_MAX_TOKENS,
        },
        "summarizer": {
            "model": cfg.SUMMARIZER_MODEL,
            "temperature": cfg.SUMMARIZER_TEMPERATURE,
            "max_tokens": cfg.SUMMARIZER_MAX_TOKENS,
        },
        "needs": {
            "model": cfg.NEEDS_MODEL,
            "temperature": cfg.NEEDS_TEMPERATURE,
            "max_tokens": cfg.NEEDS_MAX_TOKENS,
            "timeout": cfg.NEEDS_TIMEOUT,
        },
        "messaging": {
            "model": cfg.MESSAGING_MODEL,
            "temperature": cfg.MESSAGING_TEMPERATURE,
            "max_tokens": cfg.MESSAGING_MAX_TOKENS,
            "timeout": cfg.MESSAGING_TIMEOUT,
        },
        "orchestration": {
            "model": cfg.ORCHESTRATION_MODEL,
            "temperature": cfg.ORCHESTRATION_TEMPERATURE,
            "max_tokens": cfg.ORCHESTRATION_MAX_TOKENS,
            "timeout": cfg.ORCHESTRATION_TIMEOUT,
        },
        "segment_naming": {
            "model": cfg.SEGMENT_NAMING_MODEL,
            "temperature": cfg.SEGMENT_NAMING_TEMPERATURE,
            "max_tokens": cfg.SEGMENT_NAMING_MAX_TOKENS,
            "timeout": cfg.SEGMENT_NAMING_TIMEOUT,
        },
        "graph": {
            "model": cfg.GRAPH_MODEL,
            "temperature": cfg.GRAPH_TEMPERATURE,
            "max_tokens": cfg.GRAPH_MAX_TOKENS,
        },
    }

    if service_name not in service_configs:
        raise ValueError(
            f"Unknown service: {service_name}. "
            f"Available: {', '.join(service_configs.keys())}"
        )

    return service_configs[service_name]


# =========================================================================
# Validation constants - moved from discussion_summarizer.py
# =========================================================================

# Słowa kluczowe do analizy sentymentu (moved from discussion_summarizer.py)
POSITIVE_SENTIMENT_WORDS = {
    "good", "great", "excellent", "love", "like", "enjoy", "positive",
    "amazing", "wonderful", "fantastic", "best", "happy", "yes", "agree",
    "excited", "helpful", "valuable", "useful"
}

NEGATIVE_SENTIMENT_WORDS = {
    "bad", "terrible", "hate", "dislike", "awful", "worst", "negative",
    "horrible", "poor", "no", "disagree", "concern", "worried", "against",
    "confusing", "hard", "difficult"
}

# Valid tones and types for messaging (moved from persona_messaging_service.py)
VALID_MESSAGING_TONES = {"friendly", "professional", "urgent", "empathetic"}
VALID_MESSAGING_TYPES = {"email", "ad", "landing_page", "social_post"}
