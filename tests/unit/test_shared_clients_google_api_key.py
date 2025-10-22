"""
Testy pomocniczych funkcji odpowiedzialnych za rozwiązywanie klucza Google API.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import get_settings
from app.services import clients

_ENV_VARS = [
    "GOOGLE_API_KEY",
    "GOOGLE_API_KEY_FILE",
    "GOOGLE_API_KEY_PATH",
    "GOOGLE_GENAI_API_KEY",
    "GENAI_API_KEY",
]


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """Czyść cache ustawień i zmienne środowiskowe przed i po testach."""
    for var in _ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    get_settings.cache_clear()
    clients._resolve_google_api_key.cache_clear()
    yield
    for var in _ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    get_settings.cache_clear()
    clients._resolve_google_api_key.cache_clear()


def test_resolve_key_from_direct_env(monkeypatch):
    key = "AIzaTestKey1234567890123456789012345"
    monkeypatch.setenv("GOOGLE_API_KEY", key)

    resolved = clients._resolve_google_api_key()

    assert resolved == key


def test_resolve_key_from_secret_file(tmp_path: Path, monkeypatch):
    key = "AIzaFromFile123456789012345678901234"
    secret_file = tmp_path / "gemini.key"
    secret_file.write_text(f"{key}\n", encoding="utf-8")

    monkeypatch.setenv("GOOGLE_API_KEY", str(secret_file))

    resolved = clients._resolve_google_api_key()

    assert resolved == key


def test_resolve_key_from_file_env_var(tmp_path: Path, monkeypatch):
    key = "AIzaFromFileVar123456789012345678901"
    secret_file = tmp_path / "gemini_from_env.key"
    secret_file.write_text(key, encoding="utf-8")

    monkeypatch.setenv("GOOGLE_API_KEY_FILE", str(secret_file))

    resolved = clients._resolve_google_api_key()

    assert resolved == key


def test_missing_key_raises_runtime_error():
    with pytest.raises(RuntimeError):
        clients._get_google_api_key_or_raise()
