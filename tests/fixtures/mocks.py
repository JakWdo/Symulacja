"""Lightweight mock fixtures scoped for unit tests."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

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


@pytest.fixture
def mock_datetime():
    """
    Provide a helper to freeze datetime.now() inside a context manager.
    """

    class DatetimeMock:
        def __init__(self) -> None:
            self.fixed_time = None

        def __call__(self, time_str: str):
            self.fixed_time = datetime.fromisoformat(time_str)
            return patch("datetime.datetime", **{"now.return_value": self.fixed_time})

    return DatetimeMock()

