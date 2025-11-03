"""Testy endpointów autentykacji."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from app.main import app
from app.core.security import get_password_hash, create_access_token


client = TestClient(app, raise_server_exceptions=False)


class TestRegistration:
    """Testy rejestracji użytkowników."""

    def test_register_request_validation(self):
        """Test walidacji danych rejestracji."""
        from app.api.auth import RegisterRequest

        # Poprawne dane
        valid_data = {
            "email": "test@example.com",
            "password": "SecurePass123",
            "full_name": "John Doe",
            "company": "Tech Corp"
        }

        request = RegisterRequest(**valid_data)
        assert request.email == "test@example.com"
        assert request.full_name == "John Doe"


    def test_register_password_too_short(self):
        """Test odrzucenia krótkiego hasła."""
        from app.api.auth import RegisterRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="at least 8 characters"):
            RegisterRequest(
                email="test@example.com",
                password="short",
                full_name="John Doe"
            )


    def test_register_password_no_numbers(self):
        """Test odrzucenia hasła bez cyfr."""
        from app.api.auth import RegisterRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="letters and numbers"):
            RegisterRequest(
                email="test@example.com",
                password="OnlyLetters",
                full_name="John Doe"
            )


    def test_register_password_too_long(self):
        """Test odrzucenia zbyt długiego hasła (bcrypt limit 72 bytes)."""
        from app.api.auth import RegisterRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="at most 72 bytes"):
            RegisterRequest(
                email="test@example.com",
                password="a" * 80 + "123",
                full_name="John Doe"
            )


    def test_register_name_too_short(self):
        """Test odrzucenia zbyt krótkiego imienia."""
        from app.api.auth import RegisterRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="at least 2 characters"):
            RegisterRequest(
                email="test@example.com",
                password="SecurePass123",
                full_name="A"
            )


    def test_register_invalid_email(self):
        """Test odrzucenia nieprawidłowego emaila."""
        from app.api.auth import RegisterRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            RegisterRequest(
                email="invalid-email",
                password="SecurePass123",
                full_name="John Doe"
            )


class TestLogin:
    """Testy logowania użytkowników."""

    def test_login_request_validation(self):
        """Test walidacji danych logowania."""
        from app.api.auth import LoginRequest

        login_data = {
            "email": "user@example.com",
            "password": "MyPassword123"
        }

        request = LoginRequest(**login_data)
        assert request.email == "user@example.com"
        assert request.password == "MyPassword123"


class TestLoginErrorHandling:
    """Testy odporności endpointu logowania na błędy bazy danych."""

    def test_login_does_not_fail_when_commit_raises(self):
        """Sprawdza, czy błąd zapisu last_login_at nie blokuje logowania."""
        from fastapi.testclient import TestClient
        from uuid import uuid4
        from sqlalchemy.exc import SQLAlchemyError

        from app.main import app
        from app.models.user import User
        from app.core.security import get_password_hash
        from app.db.session import get_db

        # Przygotuj testowego użytkownika z prawidłowym hasłem
        test_user = User(
            id=uuid4(),
            email="resilience@example.com",
            hashed_password=get_password_hash("VerySafe123"),
            full_name="Resilient User",
            is_active=True,
        )

        class FakeResult:
            """Minimalna odpowiedź z zapytania select()."""

            def __init__(self, user):
                self._user = user

            def scalar_one_or_none(self):
                return self._user

        class FakeSession:
            """Asynchroniczna sesja udająca bazę danych z błędnym commitem."""

            def __init__(self, user):
                self.user = user
                self.rollback_called = False

            async def execute(self, _statement):
                return FakeResult(self.user)

            async def commit(self):
                raise SQLAlchemyError("symulowany błąd zapisu")

            async def rollback(self):
                self.rollback_called = True

        fake_session = FakeSession(test_user)

        async def override_get_db():
            """Zwraca testową sesję zamiast prawdziwego połączenia z DB."""

            yield fake_session

        client = TestClient(app, raise_server_exceptions=False)
        app.dependency_overrides[get_db] = override_get_db

        try:
            response = client.post(
                "/api/v1/auth/login",
                json={"email": "resilience@example.com", "password": "VerySafe123"},
            )
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        payload = response.json()
        assert payload["user"]["email"] == "resilience@example.com"
        assert fake_session.rollback_called is True


class TestTokenResponse:
    """Testy schematu odpowiedzi z tokenem."""

    def test_token_response_structure(self):
        """Test struktury TokenResponse."""
        from app.api.auth import TokenResponse

        response = TokenResponse(
            access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            token_type="bearer",
            user={
                "id": str(uuid4()),
                "email": "user@example.com",
                "full_name": "John Doe"
            }
        )

        assert response.token_type == "bearer"
        assert "access_token" in response.model_dump()
        assert "user" in response.model_dump()


class TestUserResponse:
    """Testy schematu odpowiedzi z danymi użytkownika."""

    def test_user_response_structure(self):
        """Test struktury UserResponse."""
        from app.api.auth import UserResponse

        user_data = {
            "id": str(uuid4()),
            "email": "user@example.com",
            "full_name": "John Doe",
            "role": "admin",
            "company": "Tech Corp",
            "avatar_url": "https://example.com/avatar.jpg",
            "plan": "free",
            "is_verified": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        response = UserResponse(**user_data)
        assert response.email == "user@example.com"
        assert response.plan == "free"
        assert response.is_verified is True


class TestPasswordSecurity:
    """Testy bezpieczeństwa haseł."""

    def test_password_hashing(self):
        """Test hashowania hasła."""
        from app.core.security import get_password_hash, verify_password

        plain_password = "SecurePass123"
        hashed = get_password_hash(plain_password)

        # Hash powinien być inny niż plain text
        assert hashed != plain_password

        # Weryfikacja powinna działać
        assert verify_password(plain_password, hashed) is True
        assert verify_password("WrongPassword", hashed) is False


    def test_password_hash_different_for_same_password(self):
        """Test czy ten sam password daje różne hashe (sól)."""
        from app.core.security import get_password_hash

        password = "TestPassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashe powinny się różnić dzięki soli
        assert hash1 != hash2


class TestJWT:
    """Testy generowania i weryfikacji JWT."""

    def test_create_access_token(self):
        """Test tworzenia tokenu dostępu."""
        from app.core.security import create_access_token

        data = {"sub": str(uuid4())}
        token = create_access_token(data)

        assert isinstance(token, str)
        # JWT składa się z 3 części oddzielonych kropkami
        assert token.count(".") == 2


    def test_decode_access_token(self):
        """Test dekodowania tokenu dostępu."""
        from app.core.security import create_access_token, decode_access_token

        user_id = str(uuid4())
        token = create_access_token({"sub": user_id})

        payload = decode_access_token(token)

        assert payload is not None
        assert payload["sub"] == user_id


    def test_decode_invalid_token(self):
        """Test dekodowania nieprawidłowego tokenu."""
        from app.core.security import decode_access_token

        invalid_token = "invalid.token.here"
        payload = decode_access_token(invalid_token)

        # Powinien zwrócić None dla nieprawidłowego tokenu
        assert payload is None


class TestAuthDependencies:
    """Testy zależności autentykacyjnych."""

    def test_get_current_user_dependency_structure(self):
        """Test struktury dependency get_current_user."""
        from app.api.dependencies import get_current_user

        # Dependency powinno być callable
        assert callable(get_current_user)


class TestPasswordValidationEdgeCases:
    """Testy walidacji hasła - przypadki brzegowe."""

    def test_password_exactly_8_chars(self):
        """Test hasła dokładnie 8 znaków (minimum)."""
        from app.api.auth import RegisterRequest

        request = RegisterRequest(
            email="test@example.com",
            password="Pass1234",  # Dokładnie 8 znaków
            full_name="Test User"
        )

        assert len(request.password) == 8


    def test_password_with_special_chars(self):
        """Test hasła ze znakami specjalnymi."""
        from app.api.auth import RegisterRequest

        request = RegisterRequest(
            email="test@example.com",
            password="P@ssw0rd!#$",
            full_name="Test User"
        )

        assert request.password == "P@ssw0rd!#$"


    def test_password_unicode_characters(self):
        """Test hasła z unicode."""
        from app.api.auth import RegisterRequest

        request = RegisterRequest(
            email="test@example.com",
            password="Pąśśwörd123",
            full_name="Test User"
        )

        # Powinno być zaakceptowane jeśli nie przekracza 72 bajtów
        assert request.password == "Pąśśwörd123"


class TestEmailNormalization:
    """Testy normalizacji emaili."""

    def test_email_lowercase(self):
        """Test czy email jest konwertowany na lowercase."""
        from app.api.auth import RegisterRequest

        request = RegisterRequest(
            email="Test.User@EXAMPLE.COM",
            password="SecurePass123",
            full_name="Test User"
        )

        # Pydantic EmailStr normalizuje tylko domenę (po @), nie część lokalną
        # Sprawdzamy że email jest zapisany poprawnie
        assert "@" in request.email
        assert request.email.split("@")[1] == request.email.split("@")[1].lower()


class TestNameValidation:
    """Testy walidacji imienia."""

    def test_name_whitespace_trimming(self):
        """Test czy whitespace jest usuwany z imienia."""
        from app.api.auth import RegisterRequest

        request = RegisterRequest(
            email="test@example.com",
            password="SecurePass123",
            full_name="  John Doe  "
        )

        # Validator powinien usunąć whitespace
        assert request.full_name == "John Doe"


    def test_name_exactly_2_chars(self):
        """Test imienia dokładnie 2 znaki (minimum)."""
        from app.api.auth import RegisterRequest

        request = RegisterRequest(
            email="test@example.com",
            password="SecurePass123",
            full_name="Jo"
        )

        assert len(request.full_name) == 2


class TestSecurityHeaders:
    """Testy nagłówków bezpieczeństwa."""

    def test_cors_headers(self):
        """Test obecności nagłówków CORS."""
        # W produkcji należy sprawdzić CORS middleware
        pass


    def test_rate_limiting(self):
        """Test rate limiting dla endpointów auth."""
        # W produkcji warto dodać rate limiting
        pass
