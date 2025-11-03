"""
Security utilities: password hashing, JWT tokens, API key encryption

Ten moduł zawiera funkcje bezpieczeństwa używane w całej aplikacji:
- Hashowanie haseł używając bcrypt (native library)
- Tworzenie i walidacja JWT tokenów (python-jose)
- Szyfrowanie/deszyfrowanie API keys używając Fernet (cryptography)

Wymaga zmiennych środowiskowych:
- SECRET_KEY: Klucz do podpisywania tokenów JWT (min 32 znaki)
- ALGORITHM: Algorytm JWT (domyślnie HS256)
- ACCESS_TOKEN_EXPIRE_MINUTES: Czas życia tokenu (domyślnie 30 min)
"""
from datetime import datetime, timedelta
import bcrypt
from jose import JWTError, jwt
from cryptography.fernet import Fernet
import hashlib
import base64
import os
from config import app as app_config


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Zweryfikuj hasło użytkownika

    Args:
        plain_password: Hasło w formie jawnej (z formularza logowania)
        hashed_password: Hash bcrypt z bazy danych

    Returns:
        True jeśli hasło pasuje do hashu, False w przeciwnym razie

    Example:
        >>> hashed = get_password_hash("mypassword123")
        >>> verify_password("mypassword123", hashed)
        True
        >>> verify_password("wrongpassword", hashed)
        False
    """
    plain_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    try:
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except ValueError:
        # Zły format hashu lub nieobsługiwany algorytm
        return False


def get_password_hash(password: str) -> str:
    """
    Hashuj hasło używając bcrypt

    Args:
        password: Hasło w formie jawnej

    Returns:
        Hash bcrypt (string, ~60 znaków)

    Example:
        >>> hash = get_password_hash("mypassword123")
        >>> hash.startswith("$2b$")
        True
    """
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("Password must be at most 72 bytes long for bcrypt hashing")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


# === TOKENY JWT ===
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Utwórz JWT access token

    Args:
        data: Payload do zakodowania (typowo {"sub": user_id, "email": email})
        expires_delta: Czas wygaśnięcia tokenu (domyślnie z settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    Returns:
        Zakodowany JWT token (string)

    Example:
        >>> token = create_access_token({"sub": "user-123", "email": "user@example.com"})
        >>> len(token) > 100
        True
    """
    to_encode = data.copy()

    # Dodaj timestamp wygaśnięcia
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=app_config.access_token_expire_minutes)

    to_encode.update({
        "exp": expire,  # Moment wygaśnięcia
        "iat": datetime.utcnow()  # Czas wystawienia
    })

    # Koduj JWT używając SECRET_KEY i algorytmu z settings
    secret_key = os.getenv("SECRET_KEY", app_config.secret_key)
    encoded_jwt = jwt.encode(
        to_encode,
        secret_key,
        algorithm=app_config.algorithm
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    """
    Zdekoduj i zwaliduj JWT token

    Args:
        token: JWT token string

    Returns:
        Zdekodowany payload (dict) lub None jeśli token jest nieprawidłowy/wygasły

    Example:
        >>> token = create_access_token({"sub": "user-123"})
        >>> payload = decode_access_token(token)
        >>> payload["sub"]
        'user-123'
    """
    try:
        secret_key = os.getenv("SECRET_KEY", app_config.secret_key)
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[app_config.algorithm]
        )
        return payload
    except JWTError:
        # Token nieprawidłowy, wygasły, lub zły klucz
        return None


# === SZYFROWANIE KLUCZY API ===
# Generuj klucz szyfrowania z SECRET_KEY (Fernet wymaga klucza base64 o długości 32 bajtów przed kodowaniem)
# Używamy SHA256 żeby mieć deterministyczne 32 bajty, następnie kodujemy url-safe base64
secret_key = os.getenv("SECRET_KEY", app_config.secret_key)
cipher_key_bytes = hashlib.sha256(secret_key.encode()).digest()
cipher_key_encoded = base64.urlsafe_b64encode(cipher_key_bytes)
cipher_suite = Fernet(cipher_key_encoded)


def encrypt_api_key(api_key: str) -> str:
    """
    Zaszyfruj Google API key do bezpiecznego przechowania w bazie

    Args:
        api_key: API key w formie jawnej (np. "AIza...")

    Returns:
        Zaszyfrowany klucz (base64 encoded string)

    Security:
        Używa Fernet (symmetric encryption) z kluczem wygenerowanym z SECRET_KEY.
        Zaszyfrowany klucz może być bezpiecznie przechowywany w bazie danych.

    Example:
        >>> encrypted = encrypt_api_key("AIzaSyABC123")
        >>> len(encrypted) > 50
        True
    """
    encrypted_bytes = cipher_suite.encrypt(api_key.encode())
    return encrypted_bytes.decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """
    Odszyfruj API key z bazy danych

    Args:
        encrypted_key: Zaszyfrowany klucz (z bazy danych)

    Returns:
        API key w formie jawnej

    Raises:
        cryptography.fernet.InvalidToken: Jeśli klucz nie może być odszyfrowany
            (np. zmieniony SECRET_KEY lub uszkodzone dane)

    Example:
        >>> encrypted = encrypt_api_key("AIzaSyABC123")
        >>> decrypt_api_key(encrypted)
        'AIzaSyABC123'
    """
    decrypted_bytes = cipher_suite.decrypt(encrypted_key.encode())
    return decrypted_bytes.decode()
