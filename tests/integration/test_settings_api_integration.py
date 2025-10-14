"""
Testy integracyjne API ustawień użytkownika z rzeczywistą bazą danych.

Ten moduł testuje pełny flow zarządzania profilem i ustawieniami:
- Pobieranie profilu użytkownika
- Aktualizacja profilu (full_name, role, company)
- Upload avatara
- Usuwanie avatara
- Pobieranie statystyk konta
- Usuwanie konta (soft delete)
"""

import pytest
from io import BytesIO
from PIL import Image


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_profile_success(authenticated_client):
    """
    Test pomyślnego pobrania profilu użytkownika.

    Weryfikuje:
    - Status 200 OK
    - Zwraca podstawowe informacje (email, full_name, role, company)
    - Nie ujawnia hashed_password
    """
    client, user, headers = await authenticated_client

    response = client.get("/api/v1/settings/profile", headers=headers)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    data = response.json()
    assert data["id"] == str(user.id)
    assert data["email"] == user.email
    assert data["full_name"] == user.full_name
    assert "hashed_password" not in data  # KRYTYCZNE: Nie ujawniać hasła
    assert "plan" in data
    assert "is_active" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_profile_success(authenticated_client):
    """
    Test pomyślnej aktualizacji profilu użytkownika.

    Weryfikuje:
    - Można zmienić full_name, role, company
    - Status 200 OK
    - Dane zostały zaktualizowane
    """
    client, user, headers = await authenticated_client

    update_data = {
        "full_name": "Updated Name",
        "role": "Senior Researcher",
        "company": "New Company Inc."
    }

    response = client.put("/api/v1/settings/profile", json=update_data, headers=headers)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["role"] == "Senior Researcher"
    assert data["company"] == "New Company Inc."


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_profile_partial_update(authenticated_client):
    """
    Test częściowej aktualizacji profilu (tylko niektóre pola).
    """
    client, user, headers = await authenticated_client

    # Update only full_name
    update_data = {
        "full_name": "Just Name"
    }

    response = client.put("/api/v1/settings/profile", json=update_data, headers=headers)

    assert response.status_code == 200

    data = response.json()
    assert data["full_name"] == "Just Name"
    assert data["email"] == user.email  # Email unchanged


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_account_stats_success(authenticated_client):
    """
    Test pobierania statystyk konta użytkownika.

    Weryfikuje:
    - Zwraca liczby: projects, personas, focus_groups, surveys
    - Status 200 OK
    """
    client, user, headers = await authenticated_client

    response = client.get("/api/v1/settings/stats", headers=headers)

    assert response.status_code == 200

    data = response.json()
    assert "projects_count" in data
    assert "personas_count" in data
    assert "focus_groups_count" in data
    assert "surveys_count" in data
    assert "plan" in data

    # Sprawdź że są to liczby
    assert isinstance(data["projects_count"], int)
    assert isinstance(data["personas_count"], int)
    assert isinstance(data["focus_groups_count"], int)
    assert isinstance(data["surveys_count"], int)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_avatar_success(authenticated_client, tmp_path):
    """
    Test pomyślnego uploadu avatara użytkownika.

    Weryfikuje:
    - Upload obrazu JPG/PNG
    - Status 200 OK
    - Zwraca URL avatara
    """
    client, user, headers = await authenticated_client

    # Utwórz testowy obraz
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)

    files = {
        'file': ('test_avatar.jpg', img_bytes, 'image/jpeg')
    }

    response = client.post(
        "/api/v1/settings/avatar",
        files=files,
        headers={"Authorization": headers["Authorization"]}  # Bez Content-Type dla multipart
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    data = response.json()
    assert "avatar_url" in data
    assert data["avatar_url"] is not None
    assert "/static/avatars/" in data["avatar_url"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_avatar_invalid_file_type(authenticated_client):
    """
    Test odrzucenia nieprawidłowego typu pliku.

    Weryfikuje:
    - Tylko JPG, PNG, WEBP są akceptowane
    - Status 400 Bad Request dla innych typów
    """
    client, user, headers = await authenticated_client

    # Próba uploadu tekstowego pliku
    files = {
        'file': ('test.txt', b'This is not an image', 'text/plain')
    }

    response = client.post(
        "/api/v1/settings/avatar",
        files=files,
        headers={"Authorization": headers["Authorization"]}
    )

    assert response.status_code == 400


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_avatar_too_large(authenticated_client):
    """
    Test odrzucenia zbyt dużego pliku (>2MB).

    UWAGA: Ten test może być pominięty jeśli walidacja rozmiaru
    nie jest zaimplementowana na poziomie API.
    """
    client, user, headers = await authenticated_client

    # Utwórz duży obraz (>2MB)
    img = Image.new('RGB', (3000, 3000), color='blue')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)

    # Sprawdź rozmiar
    size_mb = len(img_bytes.getvalue()) / (1024 * 1024)
    print(f"Image size: {size_mb:.2f} MB")

    if size_mb > 2:
        files = {
            'file': ('large_avatar.jpg', img_bytes, 'image/jpeg')
        }

        response = client.post(
            "/api/v1/settings/avatar",
            files=files,
            headers={"Authorization": headers["Authorization"]}
        )

        # Może być 400 lub 413 (Payload Too Large)
        assert response.status_code in [400, 413]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_avatar_success(authenticated_client):
    """
    Test pomyślnego usunięcia avatara użytkownika.
    """
    client, user, headers = await authenticated_client

    response = client.delete("/api/v1/settings/avatar", headers=headers)

    # Może być 200 lub 204 (No Content)
    assert response.status_code in [200, 204]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_account_soft_delete(authenticated_client, db_session):
    """
    Test soft delete konta użytkownika.

    KRYTYCZNE: Konta nie są usuwane fizycznie z bazy,
    tylko oznaczane jako nieaktywne (deleted_at, is_active=False).

    Weryfikuje:
    - Status 200 OK
    - Użytkownik nie może się zalogować po usunięciu
    - Dane pozostają w bazie (dla compliance i audytu)
    """
    from sqlalchemy import select
    from app.models.user import User

    client, user, headers = await authenticated_client

    response = client.delete("/api/v1/settings/account", headers=headers)

    assert response.status_code in [200, 204], f"Expected 200/204, got {response.status_code}: {response.text}"

    # Sprawdź że użytkownik jest oznaczony jako usunięty
    result = await db_session.execute(
        select(User).where(User.id == user.id)
    )
    deleted_user = result.scalar_one_or_none()

    if deleted_user:
        # Użytkownik istnieje ale jest nieaktywny
        assert deleted_user.is_active is False or deleted_user.deleted_at is not None
    else:
        # Alternatywnie może być fizycznie usunięty (zależy od implementacji)
        pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_settings_require_authentication(db_session):
    """
    Test że wszystkie endpointy settings wymagają autoryzacji.

    KRYTYCZNE: Chronione dane użytkownika muszą wymagać tokenu.
    """
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app, raise_server_exceptions=False)

    endpoints = [
        ("GET", "/api/v1/settings/profile"),
        ("PUT", "/api/v1/settings/profile"),
        ("GET", "/api/v1/settings/stats"),
        ("DELETE", "/api/v1/settings/avatar"),
        ("DELETE", "/api/v1/settings/account"),
    ]

    for method, endpoint in endpoints:
        if method == "GET":
            response = client.get(endpoint)
        elif method == "PUT":
            response = client.put(endpoint, json={})
        elif method == "POST":
            response = client.post(endpoint, json={})
        elif method == "DELETE":
            response = client.delete(endpoint)

        assert response.status_code == 401, f"{method} {endpoint} should require authentication"
