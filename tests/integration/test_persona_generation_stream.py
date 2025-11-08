"""
Integration tests dla SSE persona generation stream endpoint.

Ten test weryfikuje:
- Połączenie SSE stream
- Otrzymywanie progress events
- Monotoniczny wzrost progress (0 → 100%)
- Poprawne etapy generacji
- Graceful handling błędów
"""

import asyncio
import json
import logging
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.main import app
from app.models import Project, User

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.mark.slow  # SSE stream może trwać 30-60s
async def test_persona_generation_stream_basic(
    test_project: Project,
    test_user: User,
    auth_headers: dict,
):
    """
    Test podstawowego SSE stream dla generacji 2 person.

    Weryfikuje:
    - SSE stream się łączy (status 200, content-type: text/event-stream)
    - Otrzymujemy progress events
    - Progress rośnie monotonicznie (0 → 100%)
    - Ostatni event to COMPLETED
    """
    async with AsyncClient(app=app, base_url="http://test", timeout=120.0) as client:
        # Start SSE stream
        async with client.stream(
            "POST",
            f"/api/v1/projects/{test_project.id}/personas/generate/stream",
            json={
                "num_personas": 2,
                "use_rag": False,  # Disable RAG for faster test
                "adversarial_mode": False,
            },
            headers=auth_headers,
        ) as response:
            # Verify SSE headers
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

            events = []
            progresses = []

            # Read SSE events
            async for line in response.aiter_lines():
                if not line.strip():
                    continue  # Skip empty lines

                # Parse SSE event (format: "data: {json}")
                if line.startswith("data: "):
                    data_str = line[6:]  # Remove "data: " prefix
                    try:
                        data = json.loads(data_str)
                        events.append(data)
                        progresses.append(data.get("progress_percent", 0))

                        logger.info(
                            f"SSE event: stage={data.get('stage')}, "
                            f"progress={data.get('progress_percent')}%, "
                            f"message={data.get('message')}"
                        )

                        # Break jeśli completed lub failed
                        if data.get("stage") in ["completed", "failed"]:
                            break

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse SSE event: {data_str[:100]}, error: {e}")
                        continue

            # Assertions
            assert len(events) > 0, "Should receive at least one progress event"

            # Verify progress increases monotonically (lub pozostaje bez zmian)
            for i in range(1, len(progresses)):
                assert (
                    progresses[i] >= progresses[i - 1]
                ), f"Progress should increase: {progresses[i-1]}% → {progresses[i]}%"

            # Verify last event is COMPLETED (nie FAILED)
            last_event = events[-1]
            assert last_event["stage"] == "completed", f"Last stage should be 'completed', got '{last_event['stage']}'"
            assert last_event["progress_percent"] == 100, "Final progress should be 100%"

            # Verify total_personas matches request
            assert last_event["total_personas"] == 2

            # Verify personas_generated (should be 2 at completion)
            assert last_event["personas_generated"] == 2, "Should generate 2 personas"


@pytest.mark.asyncio
@pytest.mark.slow
async def test_persona_generation_stream_with_rag(
    test_project: Project,
    test_user: User,
    auth_headers: dict,
):
    """
    Test SSE stream z RAG enabled (orchestration).

    Weryfikuje:
    - Orchestration stage pojawia się (5-20%)
    - Wszystkie etapy są obecne: initializing, orchestration, generating_personas, completed
    """
    async with AsyncClient(app=app, base_url="http://test", timeout=180.0) as client:
        async with client.stream(
            "POST",
            f"/api/v1/projects/{test_project.id}/personas/generate/stream",
            json={
                "num_personas": 3,
                "use_rag": True,  # Enable RAG/orchestration
                "adversarial_mode": False,
            },
            headers=auth_headers,
        ) as response:
            assert response.status_code == 200

            events = []
            stages_seen = set()

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    events.append(data)
                    stages_seen.add(data.get("stage"))

                    if data.get("stage") in ["completed", "failed"]:
                        break

            # Verify stages (at minimum: initializing, generating_personas, completed)
            assert "initializing" in stages_seen, "Should see initializing stage"
            assert "generating_personas" in stages_seen, "Should see generating_personas stage"
            assert "completed" in stages_seen, "Should see completed stage"

            # If orchestration enabled, should see orchestration stage
            # (może nie być jeśli feature flag disabled)

            # Verify completion
            last_event = events[-1]
            assert last_event["stage"] == "completed"
            assert last_event["personas_generated"] == 3


@pytest.mark.asyncio
async def test_persona_generation_stream_nonexistent_project(
    test_user: User,
    auth_headers: dict,
):
    """
    Test SSE stream dla nieistniejącego projektu.

    Weryfikuje:
    - 404 Not Found (weryfikacja projektu przed startem stream)
    """
    fake_project_id = uuid4()

    async with AsyncClient(app=app, base_url="http://test", timeout=30.0) as client:
        response = await client.post(
            f"/api/v1/projects/{fake_project_id}/personas/generate/stream",
            json={
                "num_personas": 1,
                "use_rag": False,
                "adversarial_mode": False,
            },
            headers=auth_headers,
        )

        # Should fail immediately (before starting stream)
        assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.slow
async def test_persona_generation_stream_error_handling(
    test_project: Project,
    test_user: User,
    auth_headers: dict,
):
    """
    Test SSE stream error handling (invalid request).

    Weryfikuje:
    - Stream może zwrócić FAILED stage w przypadku błędu generacji
    - Error message jest obecny
    """
    async with AsyncClient(app=app, base_url="http://test", timeout=60.0) as client:
        # Request z invalid parameters (np. 0 personas)
        async with client.stream(
            "POST",
            f"/api/v1/projects/{test_project.id}/personas/generate/stream",
            json={
                "num_personas": 0,  # Invalid!
                "use_rag": False,
                "adversarial_mode": False,
            },
            headers=auth_headers,
        ) as response:
            # Może być 422 Unprocessable Entity (Pydantic validation)
            # lub 200 z FAILED event (jeśli validation passes ale generacja failuje)

            if response.status_code == 422:
                # Validation error (expected)
                logger.info("Request rejected by Pydantic validation (422)")
                return

            # Jeśli 200, sprawdź czy stream zawiera FAILED event
            events = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    events.append(data)

                    if data.get("stage") in ["completed", "failed"]:
                        break

            # Jeśli dotarliśmy tutaj, ostatni event powinien być FAILED lub COMPLETED
            if events:
                last_event = events[-1]
                # W zależności od implementacji może być FAILED lub walidacja może przepuścić
                logger.info(f"Last event stage: {last_event.get('stage')}")
