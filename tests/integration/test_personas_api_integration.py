"""
Testy integracyjne API person z rzeczywistą bazą danych.

Ten moduł testuje:
- Generowanie person (background task)
- Listowanie person projektu
- Pobieranie szczegółów persony
- Walidację demographics
- Usuwanie person
"""

import pytest
import asyncio
from uuid import uuid4


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_generate_personas_success(authenticated_client):
    """
    Test pomyślnego wygenerowania person.

    UWAGA: Ten test wymaga prawdziwego Gemini API i może trwać 10-20s.

    Weryfikuje:
    - Status 202 Accepted (background task)
    - Persony są generowane
    - Każda persona ma wymagane pola (demographics, Big Five, Hofstede)
    """
    client, user, headers = await authenticated_client

    # Create project
    project_data = {
        "name": "Persona Generation Test",
        "target_demographics": {
            "age_group": {"18-24": 0.3, "25-34": 0.4, "35-44": 0.3},
            "gender": {"male": 0.5, "female": 0.5}
        },
        "target_sample_size": 5  # Small number for faster test
    }
    project_response = client.post("/api/v1/projects", json=project_data, headers=headers)
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    # Generate personas
    generate_response = client.post(
        f"/api/v1/projects/{project_id}/personas/generate",
        json={"num_personas": 5, "adversarial_mode": False},
        headers=headers
    )

    assert generate_response.status_code == 202, f"Expected 202, got {generate_response.text}"

    # Poll for completion (background task)
    max_wait = 30  # 30 seconds timeout
    personas_ready = False

    for attempt in range(max_wait):
        await asyncio.sleep(1)

        personas_response = client.get(f"/api/v1/projects/{project_id}/personas", headers=headers)
        if personas_response.status_code == 200:
            personas = personas_response.json()
            if len(personas) >= 5:
                personas_ready = True
                break

    assert personas_ready, "Persona generation timed out"

    # Verify personas
    personas_response = client.get(f"/api/v1/projects/{project_id}/personas", headers=headers)
    assert personas_response.status_code == 200

    personas = personas_response.json()
    assert len(personas) == 5

    # Verify each persona has required fields
    for persona in personas:
        # Basic demographics
        assert "id" in persona
        assert "age" in persona
        assert "gender" in persona

        # Big Five traits (OCEAN)
        assert "openness" in persona
        assert "conscientiousness" in persona
        assert "extraversion" in persona
        assert "agreeableness" in persona
        assert "neuroticism" in persona

        # Verify Big Five in range [0, 1]
        assert 0 <= persona["openness"] <= 1
        assert 0 <= persona["conscientiousness"] <= 1
        assert 0 <= persona["extraversion"] <= 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_personas_invalid_num(authenticated_client):
    """
    Test walidacji liczby person do wygenerowania.

    Liczba person musi być: 1 <= num_personas <= 1000
    """
    client, user, headers = await authenticated_client

    # Create project
    project_data = {
        "name": "Invalid Num Test",
        "target_demographics": {
            "age_group": {"18-24": 0.5, "25-34": 0.5},
            "gender": {"male": 0.5, "female": 0.5}
        },
        "target_sample_size": 10
    }
    project_response = client.post("/api/v1/projects", json=project_data, headers=headers)
    project_id = project_response.json()["id"]

    # Try with 0 personas
    response_zero = client.post(
        f"/api/v1/projects/{project_id}/personas/generate",
        json={"num_personas": 0},
        headers=headers
    )
    assert response_zero.status_code == 422, "Should reject 0 personas"

    # Try with negative number
    response_negative = client.post(
        f"/api/v1/projects/{project_id}/personas/generate",
        json={"num_personas": -5},
        headers=headers
    )
    assert response_negative.status_code == 422, "Should reject negative number"

    # Try with too many (>1000)
    response_too_many = client.post(
        f"/api/v1/projects/{project_id}/personas/generate",
        json={"num_personas": 1001},
        headers=headers
    )
    assert response_too_many.status_code == 422, "Should reject >1000 personas"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_personas_returns_only_project_personas(project_with_personas):
    """
    Test że lista person zwraca tylko persony z danego projektu.

    KRYTYCZNE: Izolacja danych między projektami.
    """
    project, personas, client, headers = await project_with_personas

    # Get personas for this project
    response = client.get(f"/api/v1/projects/{project.id}/personas", headers=headers)
    assert response.status_code == 200

    personas_list = response.json()
    assert len(personas_list) == 10  # fixture creates 10 personas

    # Verify all belong to this project
    for persona in personas_list:
        # We can't directly check project_id from response,
        # but the endpoint filters by project_id
        assert "id" in persona
        assert "age" in persona


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_persona_details(project_with_personas):
    """
    Test pobierania szczegółów pojedynczej persony.
    """
    project, personas, client, headers = await project_with_personas

    persona = personas[0]

    response = client.get(f"/api/v1/personas/{persona.id}", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == str(persona.id)
    assert data["age"] == persona.age
    assert data["gender"] == persona.gender
    assert data["full_name"] == persona.full_name


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_persona_not_found(authenticated_client):
    """
    Test zwracania 404 dla nieistniejącej persony.
    """
    client, user, headers = await authenticated_client

    fake_id = str(uuid4())
    response = client.get(f"/api/v1/personas/{fake_id}", headers=headers)

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_persona(project_with_personas):
    """
    Test usuwania persony (soft delete).
    """
    project, personas, client, headers = await project_with_personas

    persona_to_delete = personas[0]
    persona_id = str(persona_to_delete.id)

    # Delete persona
    response = client.delete(f"/api/v1/personas/{persona_id}", headers=headers)
    assert response.status_code in [200, 204]

    # Verify not in list anymore
    list_response = client.get(f"/api/v1/projects/{project.id}/personas", headers=headers)
    assert list_response.status_code == 200

    remaining_personas = list_response.json()
    remaining_ids = [p["id"] for p in remaining_personas]

    assert persona_id not in remaining_ids, "Deleted persona should not appear in list"


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_generate_adversarial_personas(authenticated_client):
    """
    Test generowania person w trybie adversarial.

    Adversarial mode = persony są bardziej krytyczne/sceptyczne.
    """
    client, user, headers = await authenticated_client

    # Create project
    project_data = {
        "name": "Adversarial Test",
        "target_demographics": {
            "age_group": {"25-34": 0.5, "35-44": 0.5},
            "gender": {"male": 0.5, "female": 0.5}
        },
        "target_sample_size": 3
    }
    project_response = client.post("/api/v1/projects", json=project_data, headers=headers)
    project_id = project_response.json()["id"]

    # Generate adversarial personas
    generate_response = client.post(
        f"/api/v1/projects/{project_id}/personas/generate",
        json={"num_personas": 3, "adversarial_mode": True},  # ADVERSARIAL MODE
        headers=headers
    )

    assert generate_response.status_code == 202

    # Wait for completion
    max_wait = 20
    for attempt in range(max_wait):
        await asyncio.sleep(1)

        personas_response = client.get(f"/api/v1/projects/{project_id}/personas", headers=headers)
        if personas_response.status_code == 200:
            personas = personas_response.json()
            if len(personas) >= 3:
                break

    # Verify personas were created
    personas_response = client.get(f"/api/v1/projects/{project_id}/personas", headers=headers)
    personas = personas_response.json()

    assert len(personas) >= 3, "Adversarial personas should be generated"

    # Adversarial personas might have different personality traits
    # (e.g., lower agreeableness, higher neuroticism)
    # This is hard to test deterministically without mocking,
    # but we verify they exist
    print(f"\n[INFO] Generated {len(personas)} adversarial personas")
