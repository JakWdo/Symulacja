"""CI-friendly end-to-end smoke test that exercises the public API surface."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models import FocusGroup, Persona, PersonaResponse
from tests.factories import focus_group_payload, persona_generation_request, project_payload, unique_email

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_ci_smoke_research_flow(monkeypatch, api_client):
    """
    Walk through a trimmed-down research workflow without external services.

    The test verifies:
    - user registration and authentication
    - project creation
    - persona generation via stubbed background task
    - focus-group creation and execution via stubbed task
    - retrieval of metrics and raw transcripts
    """
    from app.api import focus_groups as focus_groups_module
    from app.api import personas as personas_module

    async def fake_generate_personas_task(
        project_id,
        num_personas,
        adversarial_mode=False,
        advanced_options=None,
        use_rag=True,
    ):
        async with AsyncSessionLocal() as session:
            for index in range(num_personas):
                persona = Persona(
                    id=uuid4(),
                    project_id=project_id,
                    age=27 + index,
                    gender="female" if index % 2 else "male",
                    location="Warsaw",
                    education_level="masters",
                    income_bracket="60k-80k",
                    occupation="Product Analyst",
                    full_name=f"CI Persona {index+1}",
                    persona_title="Automation Persona",
                    headline="Reliable synthetic persona for CI smoke tests",
                    openness=0.72,
                    conscientiousness=0.68,
                    extraversion=0.55,
                    agreeableness=0.71,
                    neuroticism=0.34,
                    power_distance=0.42,
                    individualism=0.58,
                    masculinity=0.33,
                    uncertainty_avoidance=0.49,
                    long_term_orientation=0.66,
                    indulgence=0.52,
                    values=["Innovation", "Quality"],
                    interests=["Technology", "Research"],
                    background_story="Generated in-memory to validate the persona flow.",
                    rag_context_used=False,
                )
                session.add(persona)
            await session.commit()

    async def fake_run_focus_group_task(focus_group_id):
        async with AsyncSessionLocal() as session:
            focus_group = await session.get(FocusGroup, focus_group_id)
            persona_rows = await session.execute(
                select(Persona).where(Persona.id.in_(list(focus_group.persona_ids or [])))
            )
            personas = persona_rows.scalars().all()

            now = datetime.now(timezone.utc)
            focus_group.status = "completed"
            focus_group.started_at = now
            focus_group.completed_at = now
            focus_group.total_execution_time_ms = 12_000
            focus_group.avg_response_time_ms = 900.0

            for persona in personas:
                for idx, question in enumerate(focus_group.questions or []):
                    session.add(
                        PersonaResponse(
                            id=uuid4(),
                            persona_id=persona.id,
                            focus_group_id=focus_group.id,
                            question_text=question,
                            response_text=f"[Automated #{idx+1}] Persona {persona.full_name} shares insight.",
                            response_time_ms=750 + (idx * 50),
                        )
                    )

            await session.commit()

    monkeypatch.setattr(personas_module, "_generate_personas_task", fake_generate_personas_task)
    monkeypatch.setattr(focus_groups_module, "_run_focus_group_task", fake_run_focus_group_task)

    # === Register and authenticate user ===
    register_payload = {
        "email": unique_email("ci_smoke"),
        "password": "SecurePass123",
        "full_name": "CI Smoke User",
    }
    register_response = api_client.post("/api/v1/auth/register", json=register_payload)
    assert register_response.status_code == 201
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # === Create project ===
    project_response = api_client.post(
        "/api/v1/projects",
        json=project_payload(name="CI Smoke Project", target_sample_size=6),
        headers=headers,
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    # === Trigger persona generation (stubbed background task) ===
    generation_response = api_client.post(
        f"/api/v1/projects/{project_id}/personas/generate",
        json=persona_generation_request(num_personas=3),
        headers=headers,
    )
    assert generation_response.status_code == 202

    personas = []
    for _ in range(20):
        await asyncio.sleep(0.1)
        personas_response = api_client.get(f"/api/v1/projects/{project_id}/personas", headers=headers)
        assert personas_response.status_code == 200
        personas = personas_response.json()
        if len(personas) >= 3:
            break
    else:
        pytest.fail("Persona generation stub did not populate personas in time.")

    persona_ids = [persona["id"] for persona in personas[:3]]

    # === Create focus group ===
    focus_group_response = api_client.post(
        f"/api/v1/projects/{project_id}/focus-groups",
        json=focus_group_payload(
            persona_ids,
            name="CI Focus Group",
            questions=[
                "How do you perceive the product concept?",
                "What would increase your likelihood of adoption?",
            ],
        ),
        headers=headers,
    )
    assert focus_group_response.status_code == 201
    focus_group_id = focus_group_response.json()["id"]

    # === Execute focus group (stubbed background task) ===
    run_response = api_client.post(f"/api/v1/focus-groups/{focus_group_id}/run", headers=headers)
    assert run_response.status_code == 202

    for _ in range(20):
        await asyncio.sleep(0.1)
        status_response = api_client.get(f"/api/v1/focus-groups/{focus_group_id}", headers=headers)
        assert status_response.status_code == 200
        status_payload = status_response.json()
        if status_payload["status"] == "completed":
            metrics = status_payload["metrics"]
            assert metrics["meets_requirements"] is True
            break
    else:
        pytest.fail("Focus group stub did not reach completed status.")

    # === Retrieve transcripts ===
    transcripts_response = api_client.get(
        f"/api/v1/focus-groups/{focus_group_id}/responses",
        headers=headers,
    )
    assert transcripts_response.status_code == 200
    transcripts = transcripts_response.json()
    assert transcripts, "Transcripts endpoint should return grouped responses."
    assert transcripts[0]["responses"], "Each question should include at least one response."
