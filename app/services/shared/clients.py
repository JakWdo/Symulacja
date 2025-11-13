"""
Wspólne fabryki klientów LLM i embeddingów.

Udostępnia pomocnicze funkcje do tworzenia instancji modeli LLM (Google, OpenAI, Anthropic)
oraz embeddingów Google, aby uniknąć duplikacji konfiguracji w serwisach.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Literal, Union

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# Conditional imports dla multi-provider support
try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from langchain_openai import AzureChatOpenAI
    AZURE_OPENAI_AVAILABLE = True
except ImportError:
    AZURE_OPENAI_AVAILABLE = False

from config import models

# Type alias dla supported providers
LLMProvider = Literal["google", "openai", "anthropic", "azure_openai"]


def build_chat_model(
    *,
    provider: LLMProvider | None = None,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    timeout: int | None = None,
    max_retries: int = 3,
    **extra: Any,
) -> Union[ChatGoogleGenerativeAI, "ChatOpenAI", "ChatAnthropic", "AzureChatOpenAI"]:
    """
    Tworzy instancję LLM chat model z uwspólnioną konfiguracją.

    Args:
        provider: LLM provider (google, openai, anthropic, azure_openai). Default: google
        model: Nazwa modelu (domyślnie z config.models.defaults.chat.model)
        temperature: Temperatura próbkująca (domyślnie z config.models.defaults.chat.temperature)
        max_tokens: Limit tokenów (domyślnie z config.models.defaults.chat.max_tokens)
        top_p: Parametr nucleus sampling (opcjonalny)
        top_k: Parametr top-k sampling (opcjonalny, tylko Google)
        timeout: Timeout zapytania w sekundach (opcjonalny)
        max_retries: Liczba ponownych prób dla rate limits (domyślnie 3)
        extra: Dodatkowe parametry przekazywane do klienta

    Returns:
        Skonfigurowana instancja chat model z retry logic.

    Raises:
        ValueError: Jeśli provider nie jest wspierany lub brakuje API key

    Note:
        Retry logic używa exponential backoff dla API rate limits.
        LangChain automatycznie obsługuje rate limit exceptions.
    """
    # Default to google if not specified
    provider = provider or "google"

    # Get defaults from config.models
    defaults = models.config.get("defaults", {}).get("chat", {})

    # Base params (common across all providers)
    base_params: dict[str, Any] = {
        "temperature": temperature if temperature is not None else defaults.get("temperature", 0.7),
        "max_retries": max_retries,
    }

    if timeout is not None:
        base_params["timeout"] = timeout
    if top_p is not None:
        base_params["top_p"] = top_p

    # Provider-specific logic
    if provider == "google":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")

        params = {
            **base_params,
            "model": model or defaults.get("model", "gemini-2.5-flash"),
            "google_api_key": api_key,
            "max_tokens": max_tokens if max_tokens is not None else defaults.get("max_tokens", 6000),
        }
        if top_k is not None:
            params["top_k"] = top_k
        params.update(extra)
        return ChatGoogleGenerativeAI(**params)

    elif provider == "openai":
        if not OPENAI_AVAILABLE:
            raise ValueError("OpenAI provider not available. Install: pip install langchain-openai")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        params = {
            **base_params,
            "model": model or "gpt-4o",
            "api_key": api_key,
            "max_tokens": max_tokens if max_tokens is not None else defaults.get("max_tokens", 6000),
        }
        params.update(extra)
        return ChatOpenAI(**params)

    elif provider == "anthropic":
        if not ANTHROPIC_AVAILABLE:
            raise ValueError("Anthropic provider not available. Install: pip install langchain-anthropic")
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        params = {
            **base_params,
            "model": model or "claude-3-5-sonnet-20241022",
            "api_key": api_key,
            "max_tokens": max_tokens if max_tokens is not None else defaults.get("max_tokens", 6000),
        }
        params.update(extra)
        return ChatAnthropic(**params)

    elif provider == "azure_openai":
        if not AZURE_OPENAI_AVAILABLE:
            raise ValueError("Azure OpenAI provider not available. Install: pip install langchain-openai")

        # Azure requires additional env vars
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

        if not all([api_key, endpoint, deployment]):
            raise ValueError(
                "Azure OpenAI requires: AZURE_OPENAI_API_KEY, "
                "AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME"
            )

        params = {
            **base_params,
            "azure_endpoint": endpoint,
            "api_key": api_key,
            "deployment_name": deployment,
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            "max_tokens": max_tokens if max_tokens is not None else defaults.get("max_tokens", 6000),
        }
        params.update(extra)
        return AzureChatOpenAI(**params)

    else:
        raise ValueError(f"Unsupported provider: {provider}. Must be one of: google, openai, anthropic, azure_openai")


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
