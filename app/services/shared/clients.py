"""
Wspólne fabryki klientów LLM i embeddingów.

Udostępnia pomocnicze funkcje do tworzenia instancji modeli Gemini oraz
embeddingów Google, aby uniknąć duplikacji konfiguracji w serwisach.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from config import models


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
        model: Nazwa modelu Gemini (domyślnie z config.models.defaults.chat.model)
        temperature: Temperatura próbkująca (domyślnie z config.models.defaults.chat.temperature)
        max_tokens: Limit tokenów (domyślnie z config.models.defaults.chat.max_tokens)
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
    # Get defaults from config.models
    defaults = models._registry.config.get("defaults", {}).get("chat", {})

    params: dict[str, Any] = {
        "model": model or defaults.get("model", "gemini-2.5-flash"),
        "google_api_key": os.getenv("GOOGLE_API_KEY"),
        "temperature": temperature if temperature is not None else defaults.get("temperature", 0.7),
        "max_tokens": max_tokens if max_tokens is not None else defaults.get("max_tokens", 6000),
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


@lru_cache(maxsize=5)  # Limit to 5 most recent embedding models (prevent unlimited growth)
def get_embeddings(model: str | None = None) -> GoogleGenerativeAIEmbeddings:
    """
    Zwraca współdzieloną instancję embeddingów Google Gemini.

    Args:
        model: Nazwa modelu embeddingowego (domyślnie z config.models.rag.embedding)

    Returns:
        Instancja GoogleGenerativeAIEmbeddings (cache'owana).
    """
    # Get embedding model from config.models
    embedding_config = models.get("rag", "embedding")
    model_name = model or embedding_config.model

    return GoogleGenerativeAIEmbeddings(
        model=model_name,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )
