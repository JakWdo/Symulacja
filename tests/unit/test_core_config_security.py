"""Testy modułów security (password hashing, JWT, encryption).

HISTORIA: Deprecated test test_get_settings_singleton został usunięty (2025-11-11)
po migracji do config/* modules w PR4. Plik zawiera teraz tylko testy security functions.
"""

import re

from app.core import security


def test_password_hashing_roundtrip():
    """Weryfikuje pełny cykl hashowania i sprawdzania hasła."""
    plain = "tajne_haslo_123"
    hashed = security.get_password_hash(plain)

    # Hash powinien mieć prefiks bcrypta i zawierać losową sól
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert security.verify_password(plain, hashed) is True
    assert security.verify_password("inne_haslo", hashed) is False


def test_password_too_long_raises():
    """Zapewnia że zbyt długie hasło rzuca ValueError."""
    with pytest.raises(ValueError):
        security.get_password_hash("a" * 80)


def test_jwt_create_and_decode(monkeypatch):
    """Sprawdza generowanie i dekodowanie tokenów JWT."""
    # Ustaw krótszy czas życia aby test był deterministyczny
    monkeypatch.setattr(security.settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 1)

    token = security.create_access_token({"sub": "user-1"})
    assert isinstance(token, str)
    assert re.match(r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$", token)

    payload = security.decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user-1"


def test_jwt_decode_invalid_token():
    """Nieprawidłowy token powinien zwrócić None zamiast wyjątku."""
    assert security.decode_access_token("niepoprawny.token.jwt") is None


def test_encrypt_decrypt_api_key_roundtrip():
    """Weryfikuje szyfrowanie oraz deszyfrowanie klucza API."""
    api_key = "AIzaSyTestKey"
    encrypted = security.encrypt_api_key(api_key)

    assert encrypted != api_key
    assert len(encrypted) > len(api_key)

    decrypted = security.decrypt_api_key(encrypted)
    assert decrypted == api_key
