"""Reusable API-level fixtures."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator, Tuple
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models import FocusGroup, Persona, PersonaResponse, Project, User


@pytest.fixture
def api_client() -> TestClient:
    """Return a TestClient instance with FastAPI exception bubbling disabled."""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Create a one-off JWT header used for authenticated requests."""
    token = create_access_token({"sub": str(uuid4())})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def authenticated_client(db_session) -> AsyncGenerator[Tuple[TestClient, User, dict[str, str]], None]:
    """
    Provide a signed-in TestClient along with a persisted user and auth headers.
    """
    test_user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password=get_password_hash("SecurePass123"),
        full_name="Test User",
        is_active=True,
    )

    db_session.add(test_user)
    await db_session.commit()
    await db_session.refresh(test_user)

    token = create_access_token({"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    client = TestClient(app, raise_server_exceptions=False)

    yield client, test_user, headers


@pytest_asyncio.fixture
async def project_with_personas(db_session, authenticated_client):
    """
    Persist a project with a deterministic set of personas ready for focus-group tests.
    """
    client, user, headers = await authenticated_client

    project = Project(
        id=uuid4(),
        owner_id=user.id,
        name="Test Project with Personas",
        description="Project for testing",
        target_audience="Test personas",
        research_objectives="Testing focus group features",
        target_sample_size=10,
    )

    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    personas = []
    for i in range(10):
        persona = Persona(
            id=uuid4(),
            project_id=project.id,
            age=25 + (i * 3),
            gender="male" if i % 2 == 0 else "female",
            full_name=f"Test Persona {i+1}",
            location="Warsaw" if i < 5 else "Krakow",
            education_level="bachelors" if i < 7 else "masters",
            income_bracket="30k-60k" if i < 5 else "60k-100k",
            occupation=f"Professional {i+1}",
            background_story=f"Persona {i+1} is a professional interested in innovation.",
            values=["Quality", "Innovation"],
            interests=["Technology", "Business"],
            openness=0.7 + (i * 0.02),
            conscientiousness=0.6 + (i * 0.02),
            extraversion=0.5 + (i * 0.02),
            agreeableness=0.65 + (i * 0.02),
            neuroticism=0.4 - (i * 0.01),
        )
        personas.append(persona)
        db_session.add(persona)

    await db_session.commit()

    for persona in personas:
        await db_session.refresh(persona)

    return project, personas, client, headers


@pytest_asyncio.fixture
async def completed_focus_group(db_session, project_with_personas):
    """
    Build a completed focus group with synthetic responses ready for analytics tests.
    """
    project, personas, client, headers = await project_with_personas

    selected_personas = personas[:5]
    persona_ids = [str(p.id) for p in selected_personas]

    questions = [
        "What do you think about this product?",
        "Would you recommend it to friends?",
        "What improvements would you suggest?",
    ]

    focus_group = FocusGroup(
        id=uuid4(),
        project_id=project.id,
        name="Test Focus Group",
        description="Completed focus group for testing",
        persona_ids=persona_ids,
        questions=questions,
        mode="normal",
        status="completed",
        started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        completed_at=datetime.now(timezone.utc),
        total_execution_time_ms=120000,
        avg_response_time_ms=2400.0,
    )

    db_session.add(focus_group)
    await db_session.commit()
    await db_session.refresh(focus_group)

    responses = []
    response_texts = [
        "I think this is a great product with innovative features.",
        "Yes, I would definitely recommend it to my colleagues.",
        "I would suggest adding more customization options.",
        "The product looks promising but needs better documentation.",
        "I'm not sure yet, need to see more features.",
    ]

    for question_idx, question in enumerate(questions):
        for persona_idx, persona in enumerate(selected_personas):
            response = PersonaResponse(
                id=uuid4(),
                focus_group_id=focus_group.id,
                persona_id=persona.id,
                question_text=question,
                response_text=response_texts[persona_idx % len(response_texts)],
                response_time_ms=2000 + (persona_idx * 200),
            )
            responses.append(response)
            db_session.add(response)

    await db_session.commit()

    for response in responses:
        await db_session.refresh(response)

    return focus_group, responses, client, headers
