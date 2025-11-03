"""Utility fixtures with cross-cutting concerns."""

import pytest


@pytest.fixture
def temp_file(tmp_path):
    """Yield a temporary file path that is cleaned up automatically."""
    file_path = tmp_path / "test_file.txt"
    yield file_path


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset cached singletons between tests to avoid state bleed."""
    yield
    from app.core.config import get_settings

    get_settings.cache_clear()


