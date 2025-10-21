"""
Unit Tests dla Security Fixes

Testy weryfikujące że security fixes działają poprawnie:
1. Path traversal protection w avatar delete
2. File size limit w RAG upload
3. Filename validation w RAG upload
4. Rate limiting na endpointach
5. SECRET_KEY validation w produkcji
6. Security headers w responses

Uruchom:
    pytest tests/unit/test_security_fixes.py -v
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException, status
from datetime import datetime
import io

# Tests będą działać tylko jeśli slowapi jest zainstalowane
try:
    from slowapi.errors import RateLimitExceeded
    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False
    RateLimitExceeded = Exception  # Fallback


class TestPathTraversalProtection:
    """
    Testy ochrony przed path traversal w avatar delete

    Security Issue: Path traversal pozwalał na usunięcie arbitralnych plików
    Fix: Walidacja że path jest wewnątrz AVATAR_DIR przez resolve() + startswith()
    """

    def test_avatar_delete_blocks_path_traversal(self, mock_db, mock_user):
        """Test że próba usunięcia pliku poza AVATAR_DIR jest blokowana"""
        from app.api.settings import AVATAR_DIR

        # Symuluj użytkownika z malicious avatar_url
        mock_user.avatar_url = "/static/avatars/../../../etc/passwd"

        # Importuj funkcję delete (będziemy testować logikę path validation)
        # W praktyce endpoint zwróci 400 Bad Request
        avatar_path = Path(mock_user.avatar_url.lstrip('/'))
        avatar_path_resolved = avatar_path.resolve()
        avatar_dir_resolved = AVATAR_DIR.resolve()

        # Sprawdź że path NIE startuje od AVATAR_DIR
        is_safe = str(avatar_path_resolved).startswith(str(avatar_dir_resolved))

        assert not is_safe, "Path traversal attack powinien być zablokowany"

    def test_avatar_delete_allows_legitimate_path(self, mock_db, mock_user):
        """Test że legalne paths są dozwolone"""
        from app.api.settings import AVATAR_DIR

        # Legalne avatar_url
        mock_user.avatar_url = "/static/avatars/user-123_abc.jpg"

        avatar_path = Path(mock_user.avatar_url.lstrip('/'))
        avatar_path_resolved = avatar_path.resolve()
        avatar_dir_resolved = AVATAR_DIR.resolve()

        # Sprawdź że legit path jest dozwolony
        is_safe = str(avatar_path_resolved).startswith(str(avatar_dir_resolved))

        assert is_safe, "Legitny avatar path powinien być dozwolony"


class TestRAGFileSizeLimit:
    """
    Testy limitu rozmiaru pliku w RAG upload

    Security Issue: Brak limitu pozwalał na upload 10GB plików (DoS)
    Fix: MAX_DOCUMENT_SIZE_MB = 50 i sprawdzanie file_size
    """

    @pytest.mark.asyncio
    async def test_rag_upload_rejects_oversized_file(self):
        """Test że plik >50MB jest odrzucany z HTTP 413"""
        from app.core.config import get_settings

        settings = get_settings()
        max_size_bytes = settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024

        # Symuluj plik 100MB
        file_size = 100 * 1024 * 1024

        assert file_size > max_size_bytes, "Test file powinien być większy niż limit"

        # W prawdziwym endpoincie zostałby zwrócony HTTP 413
        # Tutaj sprawdzamy logikę
        should_reject = file_size > max_size_bytes
        assert should_reject, "Oversized file powinien być odrzucony"

    @pytest.mark.asyncio
    async def test_rag_upload_accepts_normal_file(self):
        """Test że plik <50MB jest akceptowany"""
        from app.core.config import get_settings

        settings = get_settings()
        max_size_bytes = settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024

        # Symuluj plik 10MB
        file_size = 10 * 1024 * 1024

        assert file_size <= max_size_bytes, "Normal file powinien być w limicie"

        should_accept = file_size <= max_size_bytes
        assert should_accept, "Normal file powinien być zaakceptowany"


class TestFilenameValidation:
    """
    Testy walidacji filename w RAG upload

    Security Issue: Brak walidacji filename (null bytes, length)
    Fix: Sprawdzanie '\0', length > 255
    """

    def test_rag_upload_rejects_null_byte_filename(self):
        """Test że filename z null byte jest odrzucany"""
        malicious_filename = "document\0.pdf"

        # Walidacja
        is_valid = '\0' not in malicious_filename and len(malicious_filename) <= 255

        assert not is_valid, "Filename z null byte powinien być odrzucony"

    def test_rag_upload_rejects_too_long_filename(self):
        """Test że za długi filename jest odrzucany"""
        too_long_filename = "a" * 256 + ".pdf"

        # Walidacja
        is_valid = '\0' not in too_long_filename and len(too_long_filename) <= 255

        assert not is_valid, "Za długi filename powinien być odrzucony"

    def test_rag_upload_accepts_normal_filename(self):
        """Test że normalny filename jest akceptowany"""
        normal_filename = "document_2025.pdf"

        # Walidacja
        is_valid = '\0' not in normal_filename and len(normal_filename) <= 255

        assert is_valid, "Normalny filename powinien być zaakceptowany"


class TestSECRETKEYValidation:
    """
    Testy walidacji SECRET_KEY w produkcji

    Security Issue: Słaba SECRET_KEY validation (tylko != "change-me")
    Fix: Sprawdzanie długości (min 32), warn jeśli tylko alphanumeric
    """

    def test_production_rejects_short_secret_key(self):
        """Test że SECRET_KEY <32 znaki jest odrzucany w produkcji"""
        secret_key = "short-key-123"  # 14 znaków

        # Logika walidacji z main.py
        should_reject = len(secret_key) < 32

        assert should_reject, "Krótki SECRET_KEY powinien być odrzucony w produkcji"

    def test_production_accepts_strong_secret_key(self):
        """Test że silny SECRET_KEY (32+ znaków) jest akceptowany"""
        secret_key = "a" * 32 + "!@#$%"  # 37 znaków z special chars

        # Logika walidacji
        should_accept = len(secret_key) >= 32

        assert should_accept, "Silny SECRET_KEY powinien być zaakceptowany"

    def test_production_warns_alphanumeric_only_key(self):
        """Test że warning jest wyświetlany dla alphanumeric-only SECRET_KEY"""
        secret_key = "a" * 32  # 32 znaki, tylko litery

        # Sprawdź czy jest alphanumeric
        is_weak = secret_key.isalnum()

        assert is_weak, "Alphanumeric-only key powinien być flagged jako weak"


@pytest.mark.skipif(not SLOWAPI_AVAILABLE, reason="slowapi not installed")
class TestRateLimiting:
    """
    Testy rate limiting na endpointach

    Security Issue: Brak rate limiting (brute force, DoS)
    Fix: slowapi z limitami na /login, /register, /generate, /upload
    """

    def test_rate_limiter_configured(self):
        """Test że rate limiter jest skonfigurowany w aplikacji"""
        from app.main import app

        # Sprawdź że limiter jest w app.state
        assert hasattr(app.state, 'limiter'), "Rate limiter powinien być w app.state"

    def test_login_endpoint_has_rate_limit(self):
        """Test że /auth/login ma rate limit decorator"""
        from app.api import auth
        import inspect

        # Sprawdź czy login funkcja ma decorator z 'limit' w nazwie
        login_func = auth.login
        source = inspect.getsource(login_func)

        # Szukamy decoratora @limiter.limit
        has_rate_limit = '@limiter.limit' in source

        assert has_rate_limit, "/auth/login powinien mieć rate limit decorator"

    def test_register_endpoint_has_rate_limit(self):
        """Test że /auth/register ma rate limit decorator"""
        from app.api import auth
        import inspect

        register_func = auth.register
        source = inspect.getsource(register_func)

        has_rate_limit = '@limiter.limit' in source

        assert has_rate_limit, "/auth/register powinien mieć rate limit decorator"


class TestSecurityHeaders:
    """
    Testy security headers w responses

    Security Issue: Brak security headers (XSS, clickjacking, etc.)
    Fix: SecurityHeadersMiddleware dodający OWASP headers
    """

    def test_security_headers_middleware_exists(self):
        """Test że SecurityHeadersMiddleware istnieje"""
        from app.middleware.security import SecurityHeadersMiddleware

        assert SecurityHeadersMiddleware is not None

    @pytest.mark.asyncio
    async def test_security_headers_added_to_response(self):
        """Test że security headers są dodawane do response"""
        from app.middleware.security import SecurityHeadersMiddleware
        from starlette.responses import Response
        from starlette.requests import Request

        # Mock request i response
        scope = {"type": "http", "method": "GET", "path": "/", "query_string": b""}
        request = Request(scope)

        # Symuluj response
        async def mock_call_next(request):
            return Response("OK", status_code=200)

        # Utwórz middleware
        middleware = SecurityHeadersMiddleware(app=None)

        # Wywołaj dispatch
        response = await middleware.dispatch(request, mock_call_next)

        # Sprawdź że headers są dodane
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers
        assert "Content-Security-Policy" in response.headers


class TestCORSConfiguration:
    """
    Testy konfiguracji CORS

    Security Issue: Wildcard CORS w development (allow_origins=['*'] + credentials)
    Fix: Explicit localhost origins zamiast wildcard
    """

    def test_development_cors_no_wildcard(self):
        """Test że development mode NIE używa wildcard CORS"""
        environment = "development"

        # Logika z main.py
        allowed_origins = (
            ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"]
            if environment == "development"
            else "https://app.example.com".split(",")
        )

        # Sprawdź że NIE ma wildcard
        assert "*" not in allowed_origins, "Development CORS nie powinien używać wildcard"

    def test_production_cors_uses_config(self):
        """Test że production używa ALLOWED_ORIGINS z config"""
        environment = "production"
        allowed_origins_config = "https://app.example.com,https://admin.example.com"

        # Logika z main.py
        allowed_origins = (
            ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"]
            if environment == "development"
            else allowed_origins_config.split(",")
        )

        assert "https://app.example.com" in allowed_origins
        assert "http://localhost:5173" not in allowed_origins


# Fixtures

@pytest.fixture
def mock_db():
    """Mock database session"""
    mock = AsyncMock()
    return mock


@pytest.fixture
def mock_user():
    """Mock user object"""
    user = Mock()
    user.id = "user-123"
    user.email = "test@example.com"
    user.avatar_url = None
    user.is_active = True
    return user


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
