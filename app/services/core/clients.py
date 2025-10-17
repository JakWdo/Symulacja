"""
Wspólne fabryki klientów LLM i embeddingów.

Udostępnia pomocnicze funkcje do tworzenia instancji modeli Gemini oraz
embeddingów Google, aby uniknąć duplikacji konfiguracji w serwisach.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from app.core.config import get_settings

settings = get_settings()


def _resolve_api_key(explicit: Optional[str] = None) -> str:
    """
    Zwróć skonfigurowany Google API key lub podnieś wyjątek, jeśli go brak.

    Args:
        explicit: Opcjonalny klucz przekazany bezpośrednio w konfiguracji klienta.

    Raises:
        RuntimeError: Gdy nie skonfigurowano klucza Google Gemini.
    """
    candidate = explicit if explicit is not None else settings.GOOGLE_API_KEY
    if candidate and str(candidate).strip():
        return str(candidate).strip()
    raise RuntimeError(
        "Google Gemini API key is not configured. "
        "Ustaw zmienną środowiskową GOOGLE_API_KEY lub przekaż google_api_key w konfiguracji klienta."
    )


def build_chat_model(
    *,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    top_p: Optional[float] = None,
    top_k: Optional[int] = None,
    timeout: Optional[int] = None,
    **extra: Any,
) -> ChatGoogleGenerativeAI:
    """
    Tworzy instancję ChatGoogleGenerativeAI z uwspólnioną konfiguracją.

    Args:
        model: Nazwa modelu Gemini (domyślnie settings.DEFAULT_MODEL)
        temperature: Temperatura próbkująca (domyślnie settings.TEMPERATURE)
        max_tokens: Limit tokenów (domyślnie settings.MAX_TOKENS)
        top_p: Parametr nucleus sampling (opcjonalny)
        top_k: Parametr top-k sampling (opcjonalny)
        timeout: Timeout zapytania w sekundach (opcjonalny)
        extra: Dodatkowe parametry przekazywane do klienta

    Returns:
        Skonfigurowana instancja ChatGoogleGenerativeAI.
    """

    extra_params = dict(extra)
    explicit_key = extra_params.pop("google_api_key", None)

    params: dict[str, Any] = {
        "model": model or settings.DEFAULT_MODEL,
        "temperature": temperature if temperature is not None else settings.TEMPERATURE,
        "max_tokens": max_tokens if max_tokens is not None else settings.MAX_TOKENS,
    }

    if top_p is not None:
        params["top_p"] = top_p
    if top_k is not None:
        params["top_k"] = top_k
    if timeout is not None:
        params["timeout"] = timeout

    params["google_api_key"] = _resolve_api_key(explicit_key)
    params.update(extra_params)
    return ChatGoogleGenerativeAI(**params)


@lru_cache(maxsize=None)
def get_embeddings(model: Optional[str] = None) -> GoogleGenerativeAIEmbeddings:
    """
    Zwraca współdzieloną instancję embeddingów Google Gemini.

    Args:
        model: Nazwa modelu embeddingowego (domyślnie settings.EMBEDDING_MODEL)

    Returns:
        Instancja GoogleGenerativeAIEmbeddings (cache'owana).
    """
    model_name = model or settings.EMBEDDING_MODEL
    return GoogleGenerativeAIEmbeddings(
        model=model_name,
        google_api_key=_resolve_api_key(),
    )
