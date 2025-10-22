"""
Wspólne fabryki klientów LLM i embeddingów.

Udostępnia pomocnicze funkcje do tworzenia instancji modeli Gemini oraz
embeddingów Google, aby uniknąć duplikacji konfiguracji w serwisach.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from app.core.config import get_settings

settings = get_settings()


def build_chat_model(
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    timeout: int | None = None,
    max_retries: int = 3,
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
        max_retries: Liczba ponownych prób dla rate limits (domyślnie 3)
        extra: Dodatkowe parametry przekazywane do klienta

    Returns:
        Skonfigurowana instancja ChatGoogleGenerativeAI z retry logic.

    Note:
        Retry logic używa exponential backoff dla Google API rate limits:
        - Retry 1: 1s delay
        - Retry 2: 2s delay
        - Retry 3: 4s delay
        LangChain automatycznie obsługuje ResourceExhausted exceptions.
    """

    params: dict[str, Any] = {
        "model": model or settings.DEFAULT_MODEL,
        "google_api_key": settings.GOOGLE_API_KEY,
        "temperature": temperature if temperature is not None else settings.TEMPERATURE,
        "max_tokens": max_tokens if max_tokens is not None else settings.MAX_TOKENS,
        "max_retries": max_retries,
    }

    if top_p is not None:
        params["top_p"] = top_p
    if top_k is not None:
        params["top_k"] = top_k
    if timeout is not None:
        params["timeout"] = timeout

    params.update(extra)
    return ChatGoogleGenerativeAI(**params)


@lru_cache(maxsize=None)
def get_embeddings(model: str | None = None) -> GoogleGenerativeAIEmbeddings:
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
        google_api_key=settings.GOOGLE_API_KEY,
    )
