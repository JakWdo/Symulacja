"""Integration coverage for FastAPI authentication endpoints."""

import time
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models.user import User
from tests.factories import unique_email


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_user_success(db_session, api_client):
    """
    Test pomyślnej rejestracji nowego użytkownika.

    Weryfikuje:
    - Status 201 Created
    - Zwraca access_token
    - Zwraca user object z poprawnymi polami
    - Hasło jest zahashowane (nie plain text)
    """
    register_data = {
        "email": unique_email("register"),
        "password": "SecurePass123",
        "full_name": "New Test User",
        "company": "Test Corp"
    }

    response = api_client.post("/api/v1/auth/register", json=register_data)

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
    result = await db_session.execute(select(User).where(User.email == register_data["email"]))
    user = result.scalar_one_or_none()

    assert user is not None
    assert user.email == register_data["email"]
    # KRYTYCZNE: Hasło NIE MOŻE być plain text
    assert user.hashed_password != register_data["password"]
    assert user.hashed_password.startswith("$2b$")  # bcrypt hash


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_duplicate_email_fails(db_session, api_client):
    """
    Test że rejestracja z istniejącym emailem zwraca błąd.

    KRYTYCZNE: Duplicate emails = security issue.
    """
    register_data = {
        "email": unique_email("duplicate"),
        "password": "SecurePass123",
        "full_name": "First User"
    }

    # First registration - should succeed
    response1 = api_client.post("/api/v1/auth/register", json=register_data)
    assert response1.status_code == 201

    # Second registration with same email - should fail
    response2 = api_client.post("/api/v1/auth/register", json=register_data)
    assert response2.status_code == 400

    error = response2.json()
    assert "detail" in error
    assert "already registered" in error["detail"].lower() or "exists" in error["detail"].lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_success(db_session, api_client):
    """
    Test pomyślnego logowania z poprawnymi credentials.
    """
    # Register user first
    register_data = {
        "email": unique_email("login"),
        "password": "SecurePass123",
        "full_name": "Login Test User"
    }
    register_response = api_client.post("/api/v1/auth/register", json=register_data)
    assert register_response.status_code == 201

    # Now login
    login_data = {
        "email": register_data["email"],
        "password": "SecurePass123"
    }

    response = api_client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["email"] == login_data["email"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_wrong_password_fails(db_session, api_client):
    """
    Test że logowanie z błędnym hasłem zwraca 401.

    KRYTYCZNE: Musi zwrócić 401, nie szczegółową informację
    o tym co jest złe (security best practice).
    """
    # Register user
    register_data = {
        "email": unique_email("wrongpass"),
        "password": "CorrectPass123",
        "full_name": "Wrong Pass User"
    }
    register_response = api_client.post("/api/v1/auth/register", json=register_data)
    assert register_response.status_code == 201

    # Try login with wrong password
    login_data = {
        "email": register_data["email"],
        "password": "WrongPass123"  # Different password
    }

    response = api_client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401

    error = response.json()
    assert "detail" in error
    # Should NOT reveal whether email or password is wrong
    assert "invalid" in error["detail"].lower() or "incorrect" in error["detail"].lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_nonexistent_user_fails(db_session, api_client):
    """
    Test że logowanie nieistniejącego użytkownika zwraca 401.

    KRYTYCZNE: Musi zwrócić ten sam błąd co wrong password
    (nie ujawniać czy email istnieje).
    """
    login_data = {
        "email": "nonexistent@example.com",
        "password": "SomePass123"
    }

    response = api_client.post("/api/v1/auth/login", json=login_data)
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
async def test_get_current_user_without_token_fails(api_client):
    """
    Test że dostęp do /auth/me bez tokenu zwraca 401.

    KRYTYCZNE: Protected endpoint musi wymagać autoryzacji.
    """
    response = api_client.get("/api/v1/auth/me")
    assert response.status_code == 401

    error = response.json()
    assert "detail" in error


@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_token_returns_401(api_client):
    """
    Test że nieprawidłowy JWT token zwraca 401.
    """
    # Try with invalid token
    invalid_headers = {"Authorization": "Bearer invalid.token.here"}

    response = api_client.get("/api/v1/auth/me", headers=invalid_headers)
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_expired_token_returns_401(api_client):
    """
    Test że wygasły JWT token zwraca 401.

    UWAGA: Ten test wymaga mockowania czasu lub krótszego exp time.
    Obecnie jest symboliczny, bo standardowy JWT ma długi czas życia.
    """
    from app.core.security import create_access_token
    from datetime import timedelta
    from uuid import uuid4

    # Create token with very short expiration (-1 minute = already expired)
    token = create_access_token(
        {"sub": str(uuid4())},
        expires_delta=timedelta(minutes=-1)  # Already expired
    )

    headers = {"Authorization": f"Bearer {token}"}

    response = api_client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401

    error = response.json()
    assert "detail" in error


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_validates_password_strength(api_client):
    """
    Test że walidacja hasła odrzuca słabe hasła.

    KRYTYCZNE: Weak passwords = security vulnerability.
    """
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

        response = api_client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 422, f"Weak password '{weak_pass}' should be rejected"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_protected_endpoint_requires_auth(api_client):
    """
    Test że protected endpoint (np. /projects) wymaga autoryzacji.

    KRYTYCZNE: Wszystkie business endpoints muszą być chronione.
    """
    # Try to create project without auth
    project_data = {
        "name": "Unauthorized Project",
        "target_sample_size": 20
    }

    response = api_client.post("/api/v1/projects", json=project_data)
    assert response.status_code == 401, "Protected endpoint must require authentication"
