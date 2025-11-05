"""
Unit tests dla GeneratePersonasExecutor - persona generation node.

Testuje:
- Generacja person z config (count, demographic_preset)
- Integracja z PersonaOrchestrationService (mocked)
- Przygotowanie target demographics (config → project fallback)
- Allocation plan i grupowanie demographic
- Error handling (missing config, invalid project)
- Placeholder IDs (MVP stub)

Target coverage: 90%+ dla GeneratePersonasExecutor
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, User
from app.services.workflows.nodes.personas import GeneratePersonasExecutor


class TestGeneratePersonasExecutor:
    """Test suite dla GeneratePersonasExecutor node."""

    @pytest.mark.asyncio
    async def test_execute_generates_personas(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test personas executor generates correct number of personas."""
        # Arrange
        executor = GeneratePersonasExecutor(db_session)

        node = {
            "id": "personas-1",
            "type": "generate-personas",
            "data": {
                "config": {
                    "count": 10,
                    "project_description": "Test product research",
                }
            },
        }
        context = {
            "project_id": test_project.id,
            "workflow_id": uuid4(),
            "user_id": test_user.id,
            "results": {},
        }

        # Mock PersonaOrchestrationService
        mock_allocation_plan = MagicMock()
        mock_allocation_plan.groups = [
            MagicMock(count=5, demographics={"age": "25-34"}, brief="Group 1"),
            MagicMock(count=5, demographics={"age": "35-44"}, brief="Group 2"),
        ]

        with patch(
            "app.services.workflows.nodes.personas.PersonaOrchestrationService"
        ) as mock_orchestrator_class:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.create_persona_allocation_plan = AsyncMock(
                return_value=mock_allocation_plan
            )
            mock_orchestrator_class.return_value = mock_orchestrator

            # Act
            result = await executor.execute(node, context)

        # Assert
        assert "persona_ids" in result
        assert result["count"] == 10
        assert len(result["persona_ids"]) == 10
        assert "demographics" in result
        assert "groups" in result
        assert len(result["groups"]) == 2

    @pytest.mark.asyncio
    async def test_execute_uses_project_demographics(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test executor uses project demographics as fallback."""
        # Arrange
        executor = GeneratePersonasExecutor(db_session)

        node = {
            "id": "personas-1",
            "type": "generate-personas",
            "data": {
                "config": {
                    "count": 5,
                    "project_description": "Test",
                }
            },
        }
        context = {
            "project_id": test_project.id,
            "workflow_id": uuid4(),
            "user_id": test_user.id,
            "results": {},
        }

        # Mock allocation plan
        mock_allocation_plan = MagicMock()
        mock_allocation_plan.groups = [
            MagicMock(count=5, demographics={"age": "25-34"}, brief="Group 1"),
        ]

        with patch(
            "app.services.workflows.nodes.personas.PersonaOrchestrationService"
        ) as mock_orchestrator_class:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.create_persona_allocation_plan = AsyncMock(
                return_value=mock_allocation_plan
            )
            mock_orchestrator_class.return_value = mock_orchestrator

            # Act
            result = await executor.execute(node, context)

            # Assert - orchestrator called with project demographics
            call_kwargs = mock_orchestrator.create_persona_allocation_plan.call_args[1]
            assert "target_demographics" in call_kwargs
            # Project has target_demographics set in fixture
            assert call_kwargs["target_demographics"] is not None

    @pytest.mark.asyncio
    async def test_execute_invalid_config_missing_count(
        self,
        db_session: AsyncSession,
        test_project: Project,
    ):
        """Test executor raises error when 'count' is missing from config."""
        # Arrange
        executor = GeneratePersonasExecutor(db_session)

        node = {
            "id": "personas-1",
            "type": "generate-personas",
            "data": {
                "config": {
                    # Missing 'count'
                    "project_description": "Test",
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
        with pytest.raises(Exception) as exc_info:
            await executor.execute(node, context)

        # Pydantic validation error
        assert "count" in str(exc_info.value).lower() or "validation" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_execute_invalid_project_id(
        self,
        db_session: AsyncSession,
    ):
        """Test executor raises error when project doesn't exist."""
        # Arrange
        executor = GeneratePersonasExecutor(db_session)

        invalid_project_id = uuid4()

        node = {
            "id": "personas-1",
            "type": "generate-personas",
            "data": {
                "config": {
                    "count": 5,
                    "project_description": "Test",
                }
            },
        }
        context = {
            "project_id": invalid_project_id,
            "workflow_id": uuid4(),
            "user_id": uuid4(),
            "results": {},
        }

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await executor.execute(node, context)

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_execute_with_advanced_options(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test executor uses advanced_options to override demographics."""
        # Arrange
        executor = GeneratePersonasExecutor(db_session)

        node = {
            "id": "personas-1",
            "type": "generate-personas",
            "data": {
                "config": {
                    "count": 3,
                    "project_description": "Test",
                    "advanced_options": {
                        "age_group": {"18-24": 1.0},  # Override project demographics
                    },
                }
            },
        }
        context = {
            "project_id": test_project.id,
            "workflow_id": uuid4(),
            "user_id": test_user.id,
            "results": {},
        }

        # Mock allocation plan
        mock_allocation_plan = MagicMock()
        mock_allocation_plan.groups = [
            MagicMock(count=3, demographics={"age": "18-24"}, brief="Group 1"),
        ]

        with patch(
            "app.services.workflows.nodes.personas.PersonaOrchestrationService"
        ) as mock_orchestrator_class:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.create_persona_allocation_plan = AsyncMock(
                return_value=mock_allocation_plan
            )
            mock_orchestrator_class.return_value = mock_orchestrator

            # Act
            result = await executor.execute(node, context)

            # Assert - advanced_options applied
            call_kwargs = mock_orchestrator.create_persona_allocation_plan.call_args[1]
            assert "age_group" in call_kwargs["target_demographics"]

    @pytest.mark.asyncio
    async def test_execute_with_demographic_preset(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test executor handles demographic_preset config (currently logged as warning)."""
        # Arrange
        executor = GeneratePersonasExecutor(db_session)

        node = {
            "id": "personas-1",
            "type": "generate-personas",
            "data": {
                "config": {
                    "count": 5,
                    "project_description": "Test",
                    "demographic_preset": "poland_urban",
                }
            },
        }
        context = {
            "project_id": test_project.id,
            "workflow_id": uuid4(),
            "user_id": test_user.id,
            "results": {},
        }

        # Mock allocation plan
        mock_allocation_plan = MagicMock()
        mock_allocation_plan.groups = [
            MagicMock(count=5, demographics={"age": "25-34"}, brief="Group 1"),
        ]

        with patch(
            "app.services.workflows.nodes.personas.PersonaOrchestrationService"
        ) as mock_orchestrator_class:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.create_persona_allocation_plan = AsyncMock(
                return_value=mock_allocation_plan
            )
            mock_orchestrator_class.return_value = mock_orchestrator

            # Act
            result = await executor.execute(node, context)

            # Assert - should execute successfully (preset not implemented yet)
            assert result is not None
            assert result["count"] == 5

    @pytest.mark.asyncio
    async def test_execute_returns_groups_metadata(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test executor returns groups metadata from allocation plan."""
        # Arrange
        executor = GeneratePersonasExecutor(db_session)

        node = {
            "id": "personas-1",
            "type": "generate-personas",
            "data": {
                "config": {
                    "count": 8,
                    "project_description": "Test",
                }
            },
        }
        context = {
            "project_id": test_project.id,
            "workflow_id": uuid4(),
            "user_id": test_user.id,
            "results": {},
        }

        # Mock allocation plan z multiple groups
        mock_allocation_plan = MagicMock()
        mock_allocation_plan.groups = [
            MagicMock(
                count=4,
                demographics={"age": "25-34", "gender": "female"},
                brief="Young female professionals with tech background",
            ),
            MagicMock(
                count=4,
                demographics={"age": "35-44", "gender": "male"},
                brief="Middle-aged male managers with business focus",
            ),
        ]

        with patch(
            "app.services.workflows.nodes.personas.PersonaOrchestrationService"
        ) as mock_orchestrator_class:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.create_persona_allocation_plan = AsyncMock(
                return_value=mock_allocation_plan
            )
            mock_orchestrator_class.return_value = mock_orchestrator

            # Act
            result = await executor.execute(node, context)

        # Assert
        assert "groups" in result
        assert len(result["groups"]) == 2
        assert result["groups"][0]["count"] == 4
        assert result["groups"][1]["count"] == 4
        assert "demographics" in result["groups"][0]
        assert "brief" in result["groups"][0]

    @pytest.mark.asyncio
    async def test_execute_truncates_long_briefs(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test executor truncates long briefs to 200 chars for storage."""
        # Arrange
        executor = GeneratePersonasExecutor(db_session)

        node = {
            "id": "personas-1",
            "type": "generate-personas",
            "data": {
                "config": {
                    "count": 3,
                    "project_description": "Test",
                }
            },
        }
        context = {
            "project_id": test_project.id,
            "workflow_id": uuid4(),
            "user_id": test_user.id,
            "results": {},
        }

        # Mock allocation plan z long brief
        long_brief = "A" * 500  # 500 chars
        mock_allocation_plan = MagicMock()
        mock_allocation_plan.groups = [
            MagicMock(
                count=3,
                demographics={"age": "25-34"},
                brief=long_brief,
            ),
        ]

        with patch(
            "app.services.workflows.nodes.personas.PersonaOrchestrationService"
        ) as mock_orchestrator_class:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.create_persona_allocation_plan = AsyncMock(
                return_value=mock_allocation_plan
            )
            mock_orchestrator_class.return_value = mock_orchestrator

            # Act
            result = await executor.execute(node, context)

        # Assert - brief truncated to 200 + "..."
        assert len(result["groups"][0]["brief"]) == 203  # 200 + "..."
        assert result["groups"][0]["brief"].endswith("...")

    @pytest.mark.asyncio
    async def test_execute_with_target_audience_description(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
    ):
        """Test executor passes target_audience_description to orchestrator."""
        # Arrange
        executor = GeneratePersonasExecutor(db_session)

        node = {
            "id": "personas-1",
            "type": "generate-personas",
            "data": {
                "config": {
                    "count": 5,
                    "project_description": "Test product",
                    "target_audience_description": "Tech-savvy millennials interested in sustainability",
                }
            },
        }
        context = {
            "project_id": test_project.id,
            "workflow_id": uuid4(),
            "user_id": test_user.id,
            "results": {},
        }

        # Mock allocation plan
        mock_allocation_plan = MagicMock()
        mock_allocation_plan.groups = [
            MagicMock(count=5, demographics={"age": "25-34"}, brief="Group 1"),
        ]

        with patch(
            "app.services.workflows.nodes.personas.PersonaOrchestrationService"
        ) as mock_orchestrator_class:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.create_persona_allocation_plan = AsyncMock(
                return_value=mock_allocation_plan
            )
            mock_orchestrator_class.return_value = mock_orchestrator

            # Act
            result = await executor.execute(node, context)

            # Assert - additional_context passed
            call_kwargs = mock_orchestrator.create_persona_allocation_plan.call_args[1]
            assert call_kwargs["additional_context"] == "Tech-savvy millennials interested in sustainability"
