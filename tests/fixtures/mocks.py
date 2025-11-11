"""Lightweight mock fixtures scoped for unit tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_settings():
    """Return a MagicMock with deterministic configuration attributes."""
    settings = MagicMock()
    settings.ENVIRONMENT = "test"
    settings.DEBUG = True
    settings.GOOGLE_API_KEY = "test_api_key"
    settings.DEFAULT_MODEL = "gemini-2.5-flash"
    settings.TEMPERATURE = 0.7
    settings.MAX_TOKENS = 2048
    settings.RANDOM_SEED = 42
    return settings


@pytest.fixture
def mock_llm():
    """Return an AsyncMock that mimics the LLM ainvoke interface."""
    llm = AsyncMock()
    from types import SimpleNamespace

    llm.ainvoke.return_value = SimpleNamespace(
        content="This is a mocked LLM response for testing.",
    )
    return llm



