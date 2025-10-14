"""
Testy integracyjne API autentykacji z rzeczywistą bazą danych.

Ten moduł testuje pełny flow autoryzacji:
- Rejestracja użytkowników
- Logowanie i generowanie JWT
- Ochrona endpointów
- Walidacja tokenów
- Edge cases (duplicate email, wrong password, expired tokens)
"""

import pytest
from uuid import uuid4
import time


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_user_success(db_session):
    """
    Test pomyślnej rejestracji nowego użytkownika.

    Weryfikuje:
    - Status 201 Created
    - Zwraca access_token
    - Zwraca user object z poprawnymi polami
    - Hasło jest zahashowane (nie plain text)
    """
    from fastapi.testclient import TestClient
    from app.main import app
    from sqlalchemy import select
    from app.models.user import User

    client = TestClient(app, raise_server_exceptions=False)

    register_data = {
        "email": "newuser@example.com",
        "password": "SecurePass123",
        "full_name": "New Test User",
        "company": "Test Corp"
    }

    response = client.post("/api/v1/auth/register", json=register_data)

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

    assert "user" in data
    user_data = data["user"]
    assert user_data["email"] == register_data["email"]
    assert user_data["full_name"] == register_data["full_name"]
    assert "id" in user_data

    # Verify user exists in database with hashed password
    result = await db_session.execute(
        select(User).where(User.email == register_data["email"])
    )
    user = result.scalar_one_or_none()

    assert user is not None
    assert user.email == register_data["email"]
    # KRYTYCZNE: Hasło NIE MOŻE być plain text
    assert user.hashed_password != register_data["password"]
    assert user.hashed_password.startswith("$2b$")  # bcrypt hash


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_duplicate_email_fails(db_session):
    """
    Test że rejestracja z istniejącym emailem zwraca błąd.

    KRYTYCZNE: Duplicate emails = security issue.
    """
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app, raise_server_exceptions=False)

    register_data = {
        "email": "duplicate@example.com",
        "password": "SecurePass123",
        "full_name": "First User"
    }

    # First registration - should succeed
    response1 = client.post("/api/v1/auth/register", json=register_data)
    assert response1.status_code == 201

    # Second registration with same email - should fail
    response2 = client.post("/api/v1/auth/register", json=register_data)
    assert response2.status_code == 400

    error = response2.json()
    assert "detail" in error
    assert "already registered" in error["detail"].lower() or "exists" in error["detail"].lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_success(db_session):
    """
    Test pomyślnego logowania z poprawnymi credentials.
    """
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app, raise_server_exceptions=False)

    # Register user first
    register_data = {
        "email": "logintest@example.com",
        "password": "SecurePass123",
        "full_name": "Login Test User"
    }
    register_response = client.post("/api/v1/auth/register", json=register_data)
    assert register_response.status_code == 201

    # Now login
    login_data = {
        "email": "logintest@example.com",
        "password": "SecurePass123"
    }

    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["email"] == login_data["email"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_wrong_password_fails(db_session):
    """
    Test że logowanie z błędnym hasłem zwraca 401.

    KRYTYCZNE: Musi zwrócić 401, nie szczegółową informację
    o tym co jest złe (security best practice).
    """
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app, raise_server_exceptions=False)

    # Register user
    register_data = {
        "email": "wrongpass@example.com",
        "password": "CorrectPass123",
        "full_name": "Wrong Pass User"
    }
    register_response = client.post("/api/v1/auth/register", json=register_data)
    assert register_response.status_code == 201

    # Try login with wrong password
    login_data = {
        "email": "wrongpass@example.com",
        "password": "WrongPass123"  # Different password
    }

    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401

    error = response.json()
    assert "detail" in error
    # Should NOT reveal whether email or password is wrong
    assert "invalid" in error["detail"].lower() or "incorrect" in error["detail"].lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_nonexistent_user_fails(db_session):
    """
    Test że logowanie nieistniejącego użytkownika zwraca 401.

    KRYTYCZNE: Musi zwrócić ten sam błąd co wrong password
    (nie ujawniać czy email istnieje).
    """
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app, raise_server_exceptions=False)

    login_data = {
        "email": "nonexistent@example.com",
        "password": "SomePass123"
    }

    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401

    error = response.json()
    assert "detail" in error


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_current_user_with_valid_token(authenticated_client):
    """
    Test pobierania danych zalogowanego użytkownika.
    """
    client, user, headers = await authenticated_client

    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == str(user.id)
    assert data["email"] == user.email
    assert data["full_name"] == user.full_name
    assert "hashed_password" not in data  # KRYTYCZNE: Nie ujawniać hasła


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_current_user_without_token_fails(db_session):
    """
    Test że dostęp do /auth/me bez tokenu zwraca 401.

    KRYTYCZNE: Protected endpoint musi wymagać autoryzacji.
    """
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app, raise_server_exceptions=False)

    # Try to access without Authorization header
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401

    error = response.json()
    assert "detail" in error


@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_token_returns_401(db_session):
    """
    Test że nieprawidłowy JWT token zwraca 401.
    """
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app, raise_server_exceptions=False)

    # Try with invalid token
    invalid_headers = {"Authorization": "Bearer invalid.token.here"}

    response = client.get("/api/v1/auth/me", headers=invalid_headers)
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_expired_token_returns_401(db_session):
    """
    Test że wygasły JWT token zwraca 401.

    UWAGA: Ten test wymaga mockowania czasu lub krótszego exp time.
    Obecnie jest symboliczny, bo standardowy JWT ma długi czas życia.
    """
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.security import create_access_token
    from datetime import timedelta
    from uuid import uuid4

    client = TestClient(app, raise_server_exceptions=False)

    # Create token with very short expiration (-1 minute = already expired)
    token = create_access_token(
        {"sub": str(uuid4())},
        expires_delta=timedelta(minutes=-1)  # Already expired
    )

    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401

    error = response.json()
    assert "detail" in error


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_validates_password_strength(db_session):
    """
    Test że walidacja hasła odrzuca słabe hasła.

    KRYTYCZNE: Weak passwords = security vulnerability.
    """
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app, raise_server_exceptions=False)

    weak_passwords = [
        "short",         # Za krótkie (<8 chars)
        "12345678",      # Tylko cyfry
        "abcdefgh",      # Tylko litery
        "a" * 80,        # Za długie (>72 bytes bcrypt limit)
    ]

    for weak_pass in weak_passwords:
        register_data = {
            "email": f"weakpass_{weak_pass[:5]}@example.com",
            "password": weak_pass,
            "full_name": "Weak Pass User"
        }

        response = client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 422, f"Weak password '{weak_pass}' should be rejected"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_protected_endpoint_requires_auth(db_session):
    """
    Test że protected endpoint (np. /projects) wymaga autoryzacji.

    KRYTYCZNE: Wszystkie business endpoints muszą być chronione.
    """
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app, raise_server_exceptions=False)

    # Try to create project without auth
    project_data = {
        "name": "Unauthorized Project",
        "target_demographics": {
            "age_group": {"18-24": 0.5, "25-34": 0.5},
            "gender": {"male": 0.5, "female": 0.5}
        },
        "target_sample_size": 20
    }

    response = client.post("/api/v1/projects", json=project_data)
    assert response.status_code == 401, "Protected endpoint must require authentication"
