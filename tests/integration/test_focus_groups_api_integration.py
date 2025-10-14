"""
Testy integracyjne API grup fokusowych z rzeczywistą bazą danych.

Testuje:
- Tworzenie grup fokusowych
- Aktualizację grup (draft editing)
- Uruchamianie dyskusji
- Pobieranie wyników
"""

import pytest
import asyncio


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_focus_group_success(project_with_personas):
    """Test pomyślnego utworzenia grupy fokusowej."""
    project, personas, client, headers = await project_with_personas

    persona_ids = [str(p.id) for p in personas[:5]]

    fg_data = {
        "name": "Test Focus Group",
        "description": "Testing focus group creation",
        "persona_ids": persona_ids,
        "questions": [
            "What do you think?",
            "Would you recommend it?"
        ],
        "mode": "normal"
    }

    response = client.post(
        f"/api/v1/projects/{project.id}/focus-groups",
        json=fg_data,
        headers=headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == fg_data["name"]
    assert len(data["persona_ids"]) == 5
    assert len(data["questions"]) == 2
    assert data["status"] == "pending"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_focus_group_draft(project_with_personas):
    """Test aktualizacji grupy fokusowej w statusie pending."""
    project, personas, client, headers = await project_with_personas

    # Utwórz grupę
    fg_data = {
        "name": "Original Name",
        "persona_ids": [str(personas[0].id)],
        "questions": ["Q1?"],
        "mode": "normal"
    }

    create_response = client.post(
        f"/api/v1/projects/{project.id}/focus-groups",
        json=fg_data,
        headers=headers
    )
    fg_id = create_response.json()["id"]

    # Zaktualizuj
    update_data = {
        "name": "Updated Name",
        "persona_ids": [str(personas[0].id), str(personas[1].id)],
        "questions": ["Q1?", "Q2?"],
        "mode": "adversarial"
    }

    response = client.put(
        f"/api/v1/focus-groups/{fg_id}",
        json=update_data,
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert len(data["persona_ids"]) == 2
    assert data["mode"] == "adversarial"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_focus_groups(project_with_personas):
    """Test listowania grup fokusowych projektu."""
    project, personas, client, headers = await project_with_personas

    # Utwórz 2 grupy
    for i in range(2):
        fg_data = {
            "name": f"Focus Group {i+1}",
            "persona_ids": [str(personas[0].id)],
            "questions": ["Q?"],
            "mode": "normal"
        }
        client.post(f"/api/v1/projects/{project.id}/focus-groups", json=fg_data, headers=headers)

    # Pobierz listę
    response = client.get(f"/api/v1/projects/{project.id}/focus-groups", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_focus_group_results(completed_focus_group):
    """Test pobierania wyników grupy fokusowej."""
    focus_group, responses, client, headers = await completed_focus_group

    response = client.get(
        f"/api/v1/focus-groups/{focus_group.id}/results",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "metrics" in data
