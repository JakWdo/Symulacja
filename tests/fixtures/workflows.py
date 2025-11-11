"""Workflow-specific fixtures dla testów."""

from __future__ import annotations

from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Project
from app.models.workflow import Workflow


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """
    Tworzy użytkownika testowego z unikalnym emailem.

    Args:
        db_session: Sesja bazodanowa z automatycznym rollbackiem

    Returns:
        User: Utworzony użytkownik testowy
    """
    unique_id = uuid4()
    user = User(
        id=unique_id,
        email=f"test-{unique_id}@example.com",  # Unikalny email per test
        hashed_password="hashed_password_123",
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()  # Flush zamiast commit - nie commituje transakcji
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def other_user(db_session: AsyncSession) -> User:
    """
    Tworzy drugiego użytkownika dla testów autoryzacji z unikalnym emailem.

    Args:
        db_session: Sesja bazodanowa z automatycznym rollbackiem

    Returns:
        User: Utworzony użytkownik testowy
    """
    unique_id = uuid4()
    user = User(
        id=unique_id,
        email=f"other-{unique_id}@example.com",  # Unikalny email per test
        hashed_password="hashed_password_456",
        full_name="Other User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()  # Flush zamiast commit
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_project(db_session: AsyncSession, test_user: User) -> Project:
    """
    Tworzy projekt testowy.

    Args:
        db_session: Sesja bazodanowa z automatycznym rollbackiem
        test_user: Właściciel projektu

    Returns:
        Project: Utworzony projekt testowy
    """
    project = Project(
        id=uuid4(),
        owner_id=test_user.id,
        name="Test Project",
        description="Test project description",
        target_demographics={
            "age_group": {"25-34": 0.5, "35-44": 0.5},
            "gender": {"male": 0.5, "female": 0.5},
        },
        target_sample_size=20,
        is_active=True,
    )
    db_session.add(project)
    await db_session.flush()  # Flush zamiast commit
    await db_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def test_workflow(db_session: AsyncSession, test_user: User, test_project: Project) -> Workflow:
    """
    Tworzy workflow testowy.

    Args:
        db_session: Sesja bazodanowa z automatycznym rollbackiem
        test_user: Właściciel workflow
        test_project: Projekt do którego należy workflow

    Returns:
        Workflow: Utworzony workflow testowy
    """
    workflow = Workflow(
        id=uuid4(),
        name="Test Workflow",
        description="Test workflow description",
        project_id=test_project.id,
        owner_id=test_user.id,
        canvas_data={"nodes": [], "edges": []},
        status="draft",
        is_template=False,
        is_active=True,
    )
    db_session.add(workflow)
    await db_session.flush()  # Flush zamiast commit
    await db_session.refresh(workflow)
    return workflow


@pytest_asyncio.fixture
async def test_workflow_with_canvas(
    db_session: AsyncSession, test_user: User, test_project: Project
) -> Workflow:
    """
    Tworzy workflow testowy z canvas data.

    Args:
        db_session: Sesja bazodanowa z automatycznym rollbackiem
        test_user: Właściciel workflow
        test_project: Projekt do którego należy workflow

    Returns:
        Workflow: Utworzony workflow testowy z canvas data
    """
    canvas_data = {
        "nodes": [
            {"id": "1", "type": "start", "position": {"x": 0, "y": 0}},
            {"id": "2", "type": "generate-personas", "position": {"x": 200, "y": 0}},
            {"id": "3", "type": "end", "position": {"x": 400, "y": 0}},
        ],
        "edges": [
            {"source": "1", "target": "2"},
            {"source": "2", "target": "3"},
        ],
    }

    workflow = Workflow(
        id=uuid4(),
        name="Test Workflow With Canvas",
        description="Test workflow with canvas data",
        project_id=test_project.id,
        owner_id=test_user.id,
        canvas_data=canvas_data,
        status="draft",
        is_template=False,
        is_active=True,
    )
    db_session.add(workflow)
    await db_session.flush()  # Flush zamiast commit
    await db_session.refresh(workflow)
    return workflow


@pytest_asyncio.fixture
async def test_template_workflow(
    db_session: AsyncSession, test_user: User, test_project: Project
) -> Workflow:
    """
    Tworzy workflow template dla testów read-only.

    Args:
        db_session: Sesja bazodanowa z automatycznym rollbackiem
        test_user: Właściciel workflow
        test_project: Projekt do którego należy workflow

    Returns:
        Workflow: Utworzony workflow template
    """
    workflow = Workflow(
        id=uuid4(),
        name="Template Workflow",
        description="Read-only template workflow",
        project_id=test_project.id,
        owner_id=test_user.id,
        canvas_data={"nodes": [], "edges": []},
        status="active",
        is_template=True,  # Template - read-only
        is_active=True,
    )
    db_session.add(workflow)
    await db_session.flush()  # Flush zamiast commit
    await db_session.refresh(workflow)
    return workflow
