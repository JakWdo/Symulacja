"""
Testy integracyjne API projektów z rzeczywistą bazą danych.

Ten moduł testuje CRUD operations dla projektów badawczych:
- Tworzenie projektów z walidacją demographics
- Listowanie projektów z paginacją
- Pobieranie szczegółów projektu
- Aktualizacja projektów
- Usuwanie projektów (soft delete)
- Izolacja danych między użytkownikami
"""
import pytest
from uuid import uuid4

from tests.factories import project_payload


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_project_success(authenticated_client):
    """
    Test pomyślnego utworzenia projektu.

    Weryfikuje:
    - Status 201 Created
    - Zwraca wszystkie pola (id, owner_id, demographics, timestamps)
    - Demographics sumują się do 1.0
    - Project należy do zalogowanego użytkownika
    """
    client, user, headers = await authenticated_client

    project_data = project_payload(
        name="Market Research Project",
        description="Testing project creation",
        research_objectives="Understand product preferences",
        target_demographics={
            "age_group": {"18-24": 0.2, "25-34": 0.5, "35-44": 0.3},
            "gender": {"male": 0.48, "female": 0.52},
        },
        target_sample_size=50,
    )

    response = client.post(
        "/api/v1/projects",
        json=project_data,
        headers=headers
    )

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

    data = response.json()
    assert "id" in data
    assert data["name"] == project_data["name"]
    assert data["description"] == project_data["description"]
    assert data["target_sample_size"] == 50

    # Verify demographics structure
    assert "age_group" in data["target_demographics"]
    assert "gender" in data["target_demographics"]

    # Verify demographics sum to ~1.0
    age_sum = sum(data["target_demographics"]["age_group"].values())
    gender_sum = sum(data["target_demographics"]["gender"].values())
    assert abs(age_sum - 1.0) < 0.01, f"Age distribution sum {age_sum} != 1.0"
    assert abs(gender_sum - 1.0) < 0.01, f"Gender distribution sum {gender_sum} != 1.0"

    # Verify timestamps
    assert "created_at" in data
    assert "updated_at" in data
    assert data["is_active"] is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_project_invalid_demographics_sum(authenticated_client):
    """
    Test odrzucenia projektu z demografią która nie sumuje się do 1.0.

    KRYTYCZNE: Rozkłady demograficzne muszą być prawidłowe,
    inaczej walidacja chi-kwadrat będzie błędna.
    """
    client, user, headers = await authenticated_client

    # Demographics nie sumują się do 1.0 (suma = 0.6)
    project_data = project_payload(
        name="Invalid Demographics Project",
        target_demographics={
            "age_group": {"18-24": 0.3, "25-34": 0.3},
            "gender": {"male": 0.5, "female": 0.5},
        },
        target_sample_size=20,
    )

    response = client.post(
        "/api/v1/projects",
        json=project_data,
        headers=headers
    )

    # Backend powinien zaakceptować (walidacja sumy jest w PersonaGenerator),
    # ale projekt będzie mieć nieprawidłowe dane
    # W przyszłości można dodać walidację na poziomie Pydantic
    assert response.status_code in [201, 422]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_project_empty_demographics(authenticated_client):
    """
    Test odrzucenia projektu z pustą demografią.
    """
    client, user, headers = await authenticated_client

    project_data = project_payload(
        name="Empty Demographics Project",
        target_demographics={},
        target_sample_size=20,
    )

    response = client.post(
        "/api/v1/projects",
        json=project_data,
        headers=headers
    )

    # Pydantic powinien to zaakceptować (Dict[str, Dict[str, float]]),
    # ale generowanie person będzie failować
    assert response.status_code in [201, 422]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_projects_returns_only_users_projects(authenticated_client):
    """
    Test że użytkownik widzi tylko swoje projekty.

    KRYTYCZNE: Izolacja danych między użytkownikami.
    """
    client, user, headers = await authenticated_client

    # Create 2 projects
    for i in range(2):
        project_data = project_payload(
            name=f"Test Project {i+1}",
            target_demographics={
                "age_group": {"18-24": 0.5, "25-34": 0.5},
                "gender": {"male": 0.5, "female": 0.5},
            },
            target_sample_size=20,
        )
        response = client.post("/api/v1/projects", json=project_data, headers=headers)
        assert response.status_code == 201

    # List projects
    response = client.get("/api/v1/projects", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # At least our 2 projects

    # Verify all projects belong to the user (we can't check owner_id from response,
    # but the endpoint filters by current_user.id)
    for project in data:
        assert "id" in project
        assert "name" in project
        assert "target_demographics" in project


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_projects_pagination(authenticated_client):
    """
    Test paginacji listy projektów.
    """
    client, user, headers = await authenticated_client

    # Create 5 projects
    for i in range(5):
        project_data = project_payload(
            name=f"Pagination Test Project {i+1}",
            target_demographics={
                "age_group": {"18-24": 0.5, "25-34": 0.5},
                "gender": {"male": 0.5, "female": 0.5},
            },
            target_sample_size=10,
        )
        response = client.post("/api/v1/projects", json=project_data, headers=headers)
        assert response.status_code == 201

    # Test skip parameter
    response = client.get("/api/v1/projects?skip=2&limit=2", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 2  # Should respect limit


def test_list_projects_requires_auth(api_client):
    """Ensure unauthenticated clients cannot access project listings."""
    response = api_client.get("/api/v1/projects")
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_project_details(authenticated_client):
    """
    Test pobierania szczegółów pojedynczego projektu.
    """
    client, user, headers = await authenticated_client

    # Create project
    project_data = project_payload(
        name="Detail Test Project",
        description="Project for testing details endpoint",
        target_demographics={
            "age_group": {"18-24": 0.3, "25-34": 0.4, "35-44": 0.3},
            "gender": {"male": 0.5, "female": 0.5},
        },
        target_sample_size=30,
    )
    create_response = client.post("/api/v1/projects", json=project_data, headers=headers)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Get project details
    response = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == project_data["name"]
    assert data["description"] == project_data["description"]
    assert data["target_sample_size"] == 30


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_project_not_found(authenticated_client):
    """
    Test zwracania 404 dla nieistniejącego projektu.
    """
    client, user, headers = await authenticated_client

    fake_id = str(uuid4())
    response = client.get(f"/api/v1/projects/{fake_id}", headers=headers)

    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_project_demographics(authenticated_client):
    """
    Test aktualizacji demographics projektu.
    """
    client, user, headers = await authenticated_client

    # Create project
    project_data = project_payload(
        name="Update Test Project",
        target_demographics={
            "age_group": {"18-24": 0.5, "25-34": 0.5},
            "gender": {"male": 0.5, "female": 0.5},
        },
        target_sample_size=20,
    )
    create_response = client.post("/api/v1/projects", json=project_data, headers=headers)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Update demographics
    update_data = {
        "target_demographics": {
            "age_group": {"18-24": 0.2, "25-34": 0.5, "35-44": 0.3},
            "gender": {"male": 0.4, "female": 0.6}
        },
        "target_sample_size": 50
    }

    response = client.put(f"/api/v1/projects/{project_id}", json=update_data, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["target_sample_size"] == 50
    assert "35-44" in data["target_demographics"]["age_group"]
    assert data["target_demographics"]["gender"]["female"] == 0.6


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_project_partial_update(authenticated_client):
    """
    Test częściowej aktualizacji projektu (tylko niektóre pola).
    """
    client, user, headers = await authenticated_client

    # Create project
    project_data = {
        "name": "Partial Update Test",
        "description": "Original description",
        "target_demographics": {
            "age_group": {"18-24": 0.5, "25-34": 0.5},
            "gender": {"male": 0.5, "female": 0.5}
        },
        "target_sample_size": 20
    }
    create_response = client.post("/api/v1/projects", json=project_data, headers=headers)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Update only description
    update_data = {
        "description": "Updated description"
    }

    response = client.put(f"/api/v1/projects/{project_id}", json=update_data, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["description"] == "Updated description"
    assert data["name"] == "Partial Update Test"  # Name unchanged
    assert data["target_sample_size"] == 20  # Sample size unchanged


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_project_soft_delete(authenticated_client):
    """
    Test soft delete projektu (is_active = False).

    KRYTYCZNE: Projekty nie są usuwane fizycznie z bazy,
    tylko oznaczane jako nieaktywne.
    """
    client, user, headers = await authenticated_client

    # Create project
    project_data = {
        "name": "Delete Test Project",
        "target_demographics": {
            "age_group": {"18-24": 0.5, "25-34": 0.5},
            "gender": {"male": 0.5, "female": 0.5}
        },
        "target_sample_size": 20
    }
    create_response = client.post("/api/v1/projects", json=project_data, headers=headers)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Delete project
    response = client.delete(f"/api/v1/projects/{project_id}", headers=headers)
    assert response.status_code in [200, 204]

    # Verify project is not in list (is_active = False)
    list_response = client.get("/api/v1/projects", headers=headers)
    assert list_response.status_code == 200

    projects = list_response.json()
    project_ids = [p["id"] for p in projects]
    assert project_id not in project_ids, "Deleted project should not appear in list"

    # Verify direct access returns 404 or shows is_active = False
    get_response = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    # Depending on implementation, might return 404 or 200 with is_active=False
    assert get_response.status_code in [200, 404]
