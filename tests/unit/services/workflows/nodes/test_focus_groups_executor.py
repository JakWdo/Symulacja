"""
Unit tests dla RunFocusGroupExecutor - focus group execution node.

Testuje:
- Prowadzenie focus group z participants
- Integracja z FocusGroupServiceLangChain (mocked)
- Pobieranie participant_ids (z config lub poprzedniego node)
- Walidacja person (existence check)
- Generacja pytań z topics
- FocusGroup record creation w DB
- Error handling (no participants, personas not found, service failure)

Target coverage: 90%+ dla RunFocusGroupExecutor
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FocusGroup, Persona, Project, User
from app.services.workflows.nodes.focus_groups import RunFocusGroupExecutor


class TestRunFocusGroupExecutor:
    """Test suite dla RunFocusGroupExecutor node."""

    @pytest.mark.asyncio
    async def test_execute_runs_focus_group_success(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test focus group executor runs focus group successfully."""
        # Arrange - create test personas
        persona1 = Persona(
            id=uuid4(),
            project_id=test_project.id,
            full_name="Jan Kowalski",
            age=30,
            gender="male",
            location="Warsaw",
            education_level="Master",
            income_bracket="50k-70k",
            occupation="Engineer",
            is_active=True,
        )
        persona2 = Persona(
            id=uuid4(),
            project_id=test_project.id,
            full_name="Anna Nowak",
            age=28,
            gender="female",
            location="Krakow",
            education_level="Bachelor",
            income_bracket="40k-60k",
            occupation="Designer",
            is_active=True,
        )
        db_session.add(persona1)
        db_session.add(persona2)
        await db_session.commit()

        executor = RunFocusGroupExecutor(db_session)

        node = {
            "id": "focus-1",
            "type": "run-focus-group",
            "data": {
                "config": {
                    "name": "Product Feedback Session",
                    "description": "Testing new product features",
                    "topics": ["User experience", "Pricing", "Features"],
                }
            },
        }
        context = {
            "project_id": test_project.id,
            "workflow_id": uuid4(),
            "user_id": test_user.id,
            "results": {
                "personas-1": {
                    "persona_ids": [str(persona1.id), str(persona2.id)],
                }
            },
        }

        # Mock FocusGroupServiceLangChain
        with patch(
            "app.services.workflows.nodes.focus_groups.FocusGroupServiceLangChain"
        ) as mock_fg_service_class:
            mock_fg_service = AsyncMock()
            mock_fg_service.run_focus_group = AsyncMock(
                return_value={
                    "status": "completed",
                    "metrics": {"total_execution_time_ms": 5000},
                }
            )
            mock_fg_service_class.return_value = mock_fg_service

            # Act
            result = await executor.execute(node, context)

        # Assert
        assert "focus_group_id" in result
        assert result["participant_count"] == 2
        assert result["status"] == "completed"
        assert result["total_execution_time_ms"] == 5000
        assert len(result["questions"]) == 3

        # Verify FocusGroup created in DB
        stmt = select(FocusGroup).where(FocusGroup.id == UUID(result["focus_group_id"]))
        db_result = await db_session.execute(stmt)
        focus_group = db_result.scalar_one()
        assert focus_group is not None
        assert focus_group.name == "Product Feedback Session"

    @pytest.mark.asyncio
    async def test_execute_gets_participants_from_config(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test executor uses participant_ids from config (priority over context)."""
        # Arrange - create personas
        persona1 = Persona(
            id=uuid4(),
            project_id=test_project.id,
            full_name="Test Persona 1",
            age=30,
            gender="male",
            location="Warsaw",
            education_level="Master",
            income_bracket="50k-70k",
            occupation="Engineer",
            is_active=True,
        )
        db_session.add(persona1)
        await db_session.commit()

        executor = RunFocusGroupExecutor(db_session)

        node = {
            "id": "focus-1",
            "type": "run-focus-group",
            "data": {
                "config": {
                    "name": "Test FG",
                    "topics": ["Topic 1"],
                    "participant_ids": [str(persona1.id)],  # Explicit participants
                }
            },
        }
        context = {
            "project_id": test_project.id,
            "workflow_id": uuid4(),
            "user_id": test_user.id,
            "results": {},  # No previous personas node
        }

        # Mock FG service
        with patch(
            "app.services.workflows.nodes.focus_groups.FocusGroupServiceLangChain"
        ) as mock_fg_service_class:
            mock_fg_service = AsyncMock()
            mock_fg_service.run_focus_group = AsyncMock(
                return_value={"status": "completed", "metrics": {}}
            )
            mock_fg_service_class.return_value = mock_fg_service

            # Act
            result = await executor.execute(node, context)

        # Assert - used config participant_ids
        assert result["participant_count"] == 1

    @pytest.mark.asyncio
    async def test_execute_no_participants_error(
        self,
        db_session: AsyncSession,
        test_project: Project,
    ):
        """Test executor raises error when no participant_ids found."""
        # Arrange
        executor = RunFocusGroupExecutor(db_session)

        node = {
            "id": "focus-1",
            "type": "run-focus-group",
            "data": {
                "config": {
                    "name": "Test FG",
                    "topics": ["Topic 1"],
                    # No participant_ids
                }
            },
        }
        context = {
            "project_id": test_project.id,
            "workflow_id": uuid4(),
            "user_id": uuid4(),
            "results": {},  # No previous personas
        }

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await executor.execute(node, context)

        assert "participant" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_execute_personas_not_found_error(
        self,
        db_session: AsyncSession,
        test_project: Project,
    ):
        """Test executor raises error when personas don't exist in DB."""
        # Arrange
        executor = RunFocusGroupExecutor(db_session)

        invalid_persona_id = uuid4()

        node = {
            "id": "focus-1",
            "type": "run-focus-group",
            "data": {
                "config": {
                    "name": "Test FG",
                    "topics": ["Topic 1"],
                    "participant_ids": [str(invalid_persona_id)],
                }
            },
        }
        context = {
            "project_id": test_project.id,
            "workflow_id": uuid4(),
            "user_id": uuid4(),
            "results": {},
        }

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await executor.execute(node, context)

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_execute_generates_questions_from_topics(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test executor generates questions from topics."""
        # Arrange - create persona
        persona = Persona(
            id=uuid4(),
            project_id=test_project.id,
            full_name="Test Persona",
            age=30,
            gender="male",
            location="Warsaw",
            education_level="Master",
            income_bracket="50k-70k",
            occupation="Engineer",
            is_active=True,
        )
        db_session.add(persona)
        await db_session.commit()

        executor = RunFocusGroupExecutor(db_session)

        node = {
            "id": "focus-1",
            "type": "run-focus-group",
            "data": {
                "config": {
                    "name": "Test FG",
                    "topics": ["Product design", "Pricing strategy", "Marketing channels"],
                }
            },
        }
        context = {
            "project_id": test_project.id,
            "workflow_id": uuid4(),
            "user_id": test_user.id,
            "results": {
                "personas-1": {"persona_ids": [str(persona.id)]},
            },
        }

        # Mock FG service
        with patch(
            "app.services.workflows.nodes.focus_groups.FocusGroupServiceLangChain"
        ) as mock_fg_service_class:
            mock_fg_service = AsyncMock()
            mock_fg_service.run_focus_group = AsyncMock(
                return_value={"status": "completed", "metrics": {}}
            )
            mock_fg_service_class.return_value = mock_fg_service

            # Act
            result = await executor.execute(node, context)

        # Assert - questions generated from topics
        assert len(result["questions"]) == 3
        assert "product design" in result["questions"][0].lower()
        assert "pricing strategy" in result["questions"][1].lower()
        assert "marketing channels" in result["questions"][2].lower()

    @pytest.mark.asyncio
    async def test_execute_default_questions_no_topics(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test executor uses default questions when no topics provided."""
        # Arrange - create persona
        persona = Persona(
            id=uuid4(),
            project_id=test_project.id,
            full_name="Test Persona",
            age=30,
            gender="male",
            location="Warsaw",
            education_level="Master",
            income_bracket="50k-70k",
            occupation="Engineer",
            is_active=True,
        )
        db_session.add(persona)
        await db_session.commit()

        executor = RunFocusGroupExecutor(db_session)

        node = {
            "id": "focus-1",
            "type": "run-focus-group",
            "data": {
                "config": {
                    "name": "Test FG",
                    "topics": [],  # Empty topics
                }
            },
        }
        context = {
            "project_id": test_project.id,
            "workflow_id": uuid4(),
            "user_id": test_user.id,
            "results": {
                "personas-1": {"persona_ids": [str(persona.id)]},
            },
        }

        # Mock FG service
        with patch(
            "app.services.workflows.nodes.focus_groups.FocusGroupServiceLangChain"
        ) as mock_fg_service_class:
            mock_fg_service = AsyncMock()
            mock_fg_service.run_focus_group = AsyncMock(
                return_value={"status": "completed", "metrics": {}}
            )
            mock_fg_service_class.return_value = mock_fg_service

            # Act
            result = await executor.execute(node, context)

        # Assert - default questions used
        assert len(result["questions"]) == 3
        assert "thoughts" in result["questions"][0].lower()

    @pytest.mark.asyncio
    async def test_execute_fg_service_failure(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test executor handles FocusGroupService failure and marks FG as failed."""
        # Arrange - create persona
        persona = Persona(
            id=uuid4(),
            project_id=test_project.id,
            full_name="Test Persona",
            age=30,
            gender="male",
            location="Warsaw",
            education_level="Master",
            income_bracket="50k-70k",
            occupation="Engineer",
            is_active=True,
        )
        db_session.add(persona)
        await db_session.commit()

        executor = RunFocusGroupExecutor(db_session)

        node = {
            "id": "focus-1",
            "type": "run-focus-group",
            "data": {
                "config": {
                    "name": "Test FG",
                    "topics": ["Topic 1"],
                }
            },
        }
        context = {
            "project_id": test_project.id,
            "workflow_id": uuid4(),
            "user_id": test_user.id,
            "results": {
                "personas-1": {"persona_ids": [str(persona.id)]},
            },
        }

        # Mock FG service to raise error
        with patch(
            "app.services.workflows.nodes.focus_groups.FocusGroupServiceLangChain"
        ) as mock_fg_service_class:
            mock_fg_service = AsyncMock()
            mock_fg_service.run_focus_group = AsyncMock(
                side_effect=Exception("LLM timeout")
            )
            mock_fg_service_class.return_value = mock_fg_service

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await executor.execute(node, context)

            assert "timeout" in str(exc_info.value).lower()

        # Verify FocusGroup marked as failed in DB
        stmt = select(FocusGroup).where(FocusGroup.project_id == test_project.id)
        result = await db_session.execute(stmt)
        focus_group = result.scalar_one()
        assert focus_group.status == "failed"

    @pytest.mark.asyncio
    async def test_execute_uses_default_name_from_label(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test executor uses node label as default FG name when not provided."""
        # Arrange - create persona
        persona = Persona(
            id=uuid4(),
            project_id=test_project.id,
            full_name="Test Persona",
            age=30,
            gender="male",
            location="Warsaw",
            education_level="Master",
            income_bracket="50k-70k",
            occupation="Engineer",
            is_active=True,
        )
        db_session.add(persona)
        await db_session.commit()

        executor = RunFocusGroupExecutor(db_session)

        node = {
            "id": "focus-1",
            "type": "run-focus-group",
            "data": {
                "label": "Product Discovery Session",
                "config": {
                    # No 'name' provided
                    "topics": ["Topic 1"],
                },
            },
        }
        context = {
            "project_id": test_project.id,
            "workflow_id": uuid4(),
            "user_id": test_user.id,
            "results": {
                "personas-1": {"persona_ids": [str(persona.id)]},
            },
        }

        # Mock FG service
        with patch(
            "app.services.workflows.nodes.focus_groups.FocusGroupServiceLangChain"
        ) as mock_fg_service_class:
            mock_fg_service = AsyncMock()
            mock_fg_service.run_focus_group = AsyncMock(
                return_value={"status": "completed", "metrics": {}}
            )
            mock_fg_service_class.return_value = mock_fg_service

            # Act
            result = await executor.execute(node, context)

        # Assert - name derived from label
        stmt = select(FocusGroup).where(FocusGroup.id == UUID(result["focus_group_id"]))
        db_result = await db_session.execute(stmt)
        focus_group = db_result.scalar_one()
        assert "Product Discovery Session" in focus_group.name

    @pytest.mark.asyncio
    async def test_execute_with_uuid_participant_ids(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test executor handles both string and UUID participant_ids."""
        # Arrange - create persona
        persona = Persona(
            id=uuid4(),
            project_id=test_project.id,
            full_name="Test Persona",
            age=30,
            gender="male",
            location="Warsaw",
            education_level="Master",
            income_bracket="50k-70k",
            occupation="Engineer",
            is_active=True,
        )
        db_session.add(persona)
        await db_session.commit()

        executor = RunFocusGroupExecutor(db_session)

        node = {
            "id": "focus-1",
            "type": "run-focus-group",
            "data": {
                "config": {
                    "name": "Test FG",
                    "topics": ["Topic 1"],
                    "participant_ids": [persona.id],  # UUID instead of string
                }
            },
        }
        context = {
            "project_id": test_project.id,
            "workflow_id": uuid4(),
            "user_id": test_user.id,
            "results": {},
        }

        # Mock FG service
        with patch(
            "app.services.workflows.nodes.focus_groups.FocusGroupServiceLangChain"
        ) as mock_fg_service_class:
            mock_fg_service = AsyncMock()
            mock_fg_service.run_focus_group = AsyncMock(
                return_value={"status": "completed", "metrics": {}}
            )
            mock_fg_service_class.return_value = mock_fg_service

            # Act
            result = await executor.execute(node, context)

        # Assert
        assert result["participant_count"] == 1

    @pytest.mark.asyncio
    async def test_execute_inactive_personas_rejected(
        self,
        db_session: AsyncSession,
        test_project: Project,
    ):
        """Test executor rejects inactive (soft-deleted) personas."""
        # Arrange - create inactive persona
        persona = Persona(
            id=uuid4(),
            project_id=test_project.id,
            full_name="Deleted Persona",
            age=30,
            gender="male",
            location="Warsaw",
            education_level="Master",
            income_bracket="50k-70k",
            occupation="Engineer",
            is_active=False,  # Soft-deleted
        )
        db_session.add(persona)
        await db_session.commit()

        executor = RunFocusGroupExecutor(db_session)

        node = {
            "id": "focus-1",
            "type": "run-focus-group",
            "data": {
                "config": {
                    "name": "Test FG",
                    "topics": ["Topic 1"],
                    "participant_ids": [str(persona.id)],
                }
            },
        }
        context = {
            "project_id": test_project.id,
            "workflow_id": uuid4(),
            "user_id": uuid4(),
            "results": {},
        }

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await executor.execute(node, context)

        assert "not found" in str(exc_info.value).lower() or "inactive" in str(exc_info.value).lower()
