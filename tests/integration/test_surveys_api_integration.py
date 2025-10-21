"""
Testy integracyjne API ankiet z rzeczywistą bazą danych.

Testuje:
- Tworzenie ankiet
- Listowanie ankiet
- Pobieranie szczegółów ankiety
"""

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_survey_success(project_with_personas):
    """Test pomyślnego utworzenia ankiety."""
    project, personas, client, headers = await project_with_personas

    survey_data = {
        "title": "Customer Satisfaction Survey",
        "description": "Testing survey creation",
        "questions": [
            {
                "id": "q1",
                "type": "rating-scale",
                "title": "How satisfied are you?",
                "scaleMin": 1,
                "scaleMax": 5
            },
            {
                "id": "q2",
                "type": "single-choice",
                "title": "Would you recommend?",
                "options": ["Yes", "No", "Maybe"]
            }
        ],
        "target_responses": 100
    }

    response = client.post(
        f"/api/v1/projects/{project.id}/surveys",
        json=survey_data,
        headers=headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == survey_data["title"]
    assert len(data["questions"]) == 2
    assert data["status"] == "draft"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_surveys(project_with_personas):
    """Test listowania ankiet projektu."""
    project, personas, client, headers = await project_with_personas

    # Utwórz 2 ankiety
    for i in range(2):
        survey_data = {
            "title": f"Survey {i+1}",
            "questions": [
                {
                    "id": "q1",
                    "type": "open-text",
                    "title": "Your feedback?"
                }
            ]
        }
        client.post(f"/api/v1/projects/{project.id}/surveys", json=survey_data, headers=headers)

    # Pobierz listę
    response = client.get(f"/api/v1/projects/{project.id}/surveys", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_survey_details(project_with_personas):
    """Test pobierania szczegółów ankiety."""
    project, personas, client, headers = await project_with_personas

    # Utwórz ankietę
    survey_data = {
        "title": "Detail Test Survey",
        "questions": [
            {
                "id": "q1",
                "type": "rating-scale",
                "title": "Rate this",
                "scaleMin": 1,
                "scaleMax": 10
            }
        ]
    }

    create_response = client.post(
        f"/api/v1/projects/{project.id}/surveys",
        json=survey_data,
        headers=headers
    )
    survey_id = create_response.json()["id"]

    # Pobierz szczegóły
    response = client.get(f"/api/v1/surveys/{survey_id}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == survey_id
    assert data["title"] == survey_data["title"]
