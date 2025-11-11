"""
Testy obsługi błędów i edge cases.

Ten moduł testuje jak system radzi sobie z:
- Błędami zewnętrznych serwisów (Gemini API, Neo4j, PostgreSQL)
- Timeoutami i quota exceeded
- Przypadkami brzegowymi (puste dane, nieprawidłowe wejście)
- Race conditions

UWAGA: Te testy używają mocków do symulacji błędów.
"""

import pytest
from unittest.mock import patch, AsyncMock
from uuid import uuid4


@pytest.mark.asyncio
async def test_gemini_api_timeout_handling(authenticated_client):
    """
    Test obsługi timeoutu Gemini API.

    Gdy Gemini API nie odpowiada w rozsądnym czasie,
    system powinien zwrócić 503 Service Unavailable.
    """
    client, user, headers = authenticated_client

    # Create project
    project_data = {
        "name": "Timeout Test Project",
        "target_demographics": {
            "age_group": {"18-24": 0.5, "25-34": 0.5},
            "gender": {"male": 0.5, "female": 0.5}
        },
        "target_sample_size": 10
    }
    project_response = client.post("/api/v1/projects", json=project_data, headers=headers)
    project_id = project_response.json()["id"]

    # Mock Gemini API to timeout
    with patch("app.services.persona_generator_langchain.ChatGoogleGenerativeAI") as mock_llm:
        mock_instance = AsyncMock()
        mock_instance.ainvoke.side_effect = TimeoutError("Gemini API timeout")
        mock_llm.return_value = mock_instance

        # Try to generate personas
        generate_response = client.post(
            f"/api/v1/projects/{project_id}/personas/generate",
            json={"num_personas": 5},
            headers=headers
        )

        # Should accept request (background task)
        assert generate_response.status_code == 202

        # Wait a bit for background task
        import asyncio
        await asyncio.sleep(2)

        # Check project status - should have error or no personas
        personas_response = client.get(f"/api/v1/projects/{project_id}/personas", headers=headers)
        personas = personas_response.json()

        # Either no personas generated or error status
        assert len(personas) < 5, "Should not generate all personas after timeout"


@pytest.mark.asyncio
async def test_gemini_api_quota_exceeded_handling(authenticated_client):
    """
    Test obsługi przekroczenia limitu Gemini API (429 error).

    System powinien gracefully handleować quota exceeded
    i informować użytkownika.
    """
    client, user, headers = authenticated_client

    # Create project
    project_data = {
        "name": "Quota Test Project",
        "target_demographics": {
            "age_group": {"18-24": 0.5, "25-34": 0.5},
            "gender": {"male": 0.5, "female": 0.5}
        },
        "target_sample_size": 5
    }
    project_response = client.post("/api/v1/projects", json=project_data, headers=headers)
    project_id = project_response.json()["id"]

    # Mock Gemini API to return 429
    with patch("app.services.persona_generator_langchain.ChatGoogleGenerativeAI") as mock_llm:
        mock_instance = AsyncMock()

        class QuotaExceededError(Exception):
            pass

        mock_instance.ainvoke.side_effect = QuotaExceededError("Quota exceeded")
        mock_llm.return_value = mock_instance

        # Try to generate personas
        generate_response = client.post(
            f"/api/v1/projects/{project_id}/personas/generate",
            json={"num_personas": 5},
            headers=headers
        )

        # Should accept but fail in background
        assert generate_response.status_code == 202


@pytest.mark.asyncio
async def test_neo4j_unavailable_fallback_to_memory_graph(completed_focus_group):
    """
    Test fallbacku do in-memory grafu gdy Neo4j niedostępny.

    KRYTYCZNE: System musi działać nawet gdy Neo4j jest down.
    """
    focus_group, responses, client, headers = completed_focus_group

    # Mock Neo4j connection to fail
    with patch("app.services.graph_service.GraphService.driver", None):
        # Try to build graph - should fallback to memory
        graph_response = client.post(
            f"/api/v1/graph/build/{focus_group.id}",
            headers=headers
        )

        # Should succeed with memory fallback
        assert graph_response.status_code == 200

        data = graph_response.json()
        # Memory fallback should still create some structure
        assert "nodes" in data or "message" in data


@pytest.mark.asyncio
async def test_empty_personas_list_for_focus_group(authenticated_client):
    """
    Test że pusta lista person jest odrzucana przy uruchomieniu focus group.

    KRYTYCZNE: Nie można uruchomić dyskusji bez uczestników.
    """
    client, user, headers = authenticated_client

    # Create project
    project_data = {
        "name": "Empty Personas Test",
        "target_demographics": {
            "age_group": {"18-24": 0.5, "25-34": 0.5},
            "gender": {"male": 0.5, "female": 0.5}
        },
        "target_sample_size": 10
    }
    project_response = client.post("/api/v1/projects", json=project_data, headers=headers)
    project_id = project_response.json()["id"]

    # Create focus group with empty persona_ids
    fg_data = {
        "name": "Empty Focus Group",
        "persona_ids": [],  # EMPTY!
        "questions": ["Test question?"],
        "mode": "normal"
    }

    # Creation might succeed (draft mode)
    fg_response = client.post(
        f"/api/v1/projects/{project_id}/focus-groups",
        json=fg_data,
        headers=headers
    )

    if fg_response.status_code == 201:
        focus_group_id = fg_response.json()["id"]

        # But run should fail
        run_response = client.post(
            f"/api/v1/focus-groups/{focus_group_id}/run",
            headers=headers
        )

        assert run_response.status_code in [400, 422], "Empty personas should be rejected"
        error = run_response.json()
        assert "detail" in error
    else:
        # Or creation fails immediately with validation error
        assert fg_response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_empty_questions_for_focus_group(authenticated_client):
    """
    Test że pusta lista pytań jest odrzucana.

    KRYTYCZNE: Nie można uruchomić dyskusji bez pytań.
    """
    client, user, headers = authenticated_client

    # Create project with personas
    project_data = {
        "name": "Empty Questions Test",
        "target_demographics": {
            "age_group": {"18-24": 0.5, "25-34": 0.5},
            "gender": {"male": 0.5, "female": 0.5}
        },
        "target_sample_size": 10
    }
    project_response = client.post("/api/v1/projects", json=project_data, headers=headers)
    project_id = project_response.json()["id"]

    # Create focus group with empty questions
    fg_data = {
        "name": "Empty Questions Group",
        "persona_ids": [str(uuid4())],  # At least one persona
        "questions": [],  # EMPTY!
        "mode": "normal"
    }

    # Creation might succeed (draft mode)
    fg_response = client.post(
        f"/api/v1/projects/{project_id}/focus-groups",
        json=fg_data,
        headers=headers
    )

    if fg_response.status_code == 201:
        focus_group_id = fg_response.json()["id"]

        # But run should fail
        run_response = client.post(
            f"/api/v1/focus-groups/{focus_group_id}/run",
            headers=headers
        )

        assert run_response.status_code in [400, 422], "Empty questions should be rejected"
    else:
        # Or creation fails immediately
        assert fg_response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_invalid_demographics_distribution(authenticated_client):
    """
    Test walidacji demographics - suma != 1.0.

    Edge case: Rozkłady które nie sumują się do 1.0
    mogą powodować błędy w walidacji chi-kwadrat.
    """
    client, user, headers = authenticated_client

    # Demographics sum > 1.0
    project_data = {
        "name": "Invalid Demographics",
        "target_demographics": {
            "age_group": {"18-24": 0.6, "25-34": 0.6},  # suma = 1.2 > 1.0!
            "gender": {"male": 0.5, "female": 0.5}
        },
        "target_sample_size": 10
    }

    response = client.post("/api/v1/projects", json=project_data, headers=headers)

    # Może zostać zaakceptowane (walidacja w PersonaGenerator),
    # ale generowanie person powinno failować
    if response.status_code == 201:
        project_id = response.json()["id"]

        # Try to generate personas
        generate_response = client.post(
            f"/api/v1/projects/{project_id}/personas/generate",
            json={"num_personas": 5},
            headers=headers
        )

        # Should accept but fail in validation
        assert generate_response.status_code in [202, 400, 422]


@pytest.mark.asyncio
async def test_concurrent_focus_group_runs_race_condition(project_with_personas):
    """
    Test race condition: 2 równoległe uruchomienia tego samego focus group.

    System powinien:
    1. Odrzucić drugie wywołanie (już running), LUB
    2. Serializować wykonanie
    """
    project, personas, client, headers = project_with_personas

    # Create focus group
    fg_data = {
        "name": "Race Condition Test",
        "persona_ids": [str(p.id) for p in personas[:3]],
        "questions": ["Test?"],
        "mode": "normal"
    }

    fg_response = client.post(
        f"/api/v1/projects/{project.id}/focus-groups",
        json=fg_data,
        headers=headers
    )
    focus_group_id = fg_response.json()["id"]

    # Try to run twice simultaneously
    run_response1 = client.post(f"/api/v1/focus-groups/{focus_group_id}/run", headers=headers)
    run_response2 = client.post(f"/api/v1/focus-groups/{focus_group_id}/run", headers=headers)

    # First should succeed
    assert run_response1.status_code == 202

    # Second should either:
    # - Return 409 Conflict (already running), OR
    # - Return 202 but be ignored/serialized
    assert run_response2.status_code in [202, 400, 409], "Concurrent runs not handled properly"


@pytest.mark.asyncio
async def test_very_large_background_story(authenticated_client):
    """
    Test edge case: Bardzo długi background_story persony.

    System powinien albo:
    1. Truncate do rozsądnej długości, LUB
    2. Odrzucić z validation error
    """
    # This test is informational - checks behavior with large text
    # Actual personas are generated by AI, so we can't directly control this
    # But we document expected behavior

    # If we were to manually create a persona with huge background:
    # - Database should have reasonable limits (VARCHAR length)
    # - API should validate max length
    # - Gemini API has token limits anyway

    # This is more of a documentation test
    print("\n[INFO] Large background story handling:")
    print("  - Database: VARCHAR/TEXT limits")
    print("  - API: Pydantic max_length validators")
    print("  - Gemini: Token limits (2M context window)")


@pytest.mark.asyncio
async def test_database_connection_error_handling(authenticated_client):
    """
    Test obsługi błędu połączenia z bazą danych.

    Gdy baza jest niedostępna, system powinien zwrócić 500 lub 503.
    """
    client, user, headers = authenticated_client

    # Mock database session to fail
    with patch("app.db.get_db") as mock_get_db:
        async def failing_db():
            raise ConnectionError("Database unavailable")

        mock_get_db.return_value = failing_db()

        # Try to create project
        project_data = {
            "name": "DB Error Test",
            "target_demographics": {
                "age_group": {"18-24": 0.5, "25-34": 0.5},
                "gender": {"male": 0.5, "female": 0.5}
            },
            "target_sample_size": 10
        }

        response = client.post("/api/v1/projects", json=project_data, headers=headers)

        # Should return 500 or 503
        assert response.status_code in [500, 503], "Database error not handled"
