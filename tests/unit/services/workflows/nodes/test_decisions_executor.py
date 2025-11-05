"""
Unit tests dla DecisionExecutor - conditional branching node.

Testuje:
- Ewaluacja prostych warunków (persona_count > 10, etc.)
- Zwracanie branch (true/false)
- Building eval context z previous results
- Safe eval z restricted builtins
- Złożone warunki (AND, OR, comparisons)
- Error handling (invalid syntax, missing variables)
- Allowlisted funkcje (len, str, int, bool)
- Security - brak dostępu do __import__, exec, open

Target coverage: 95%+ dla DecisionExecutor
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.workflows.nodes.decisions import DecisionExecutor


class TestDecisionExecutor:
    """Test suite dla DecisionExecutor node."""

    @pytest.mark.asyncio
    async def test_execute_true_condition(self, db_session: AsyncSession):
        """Test decision executor returns true branch when condition is true."""
        # Arrange
        executor = DecisionExecutor(db_session)

        node = {
            "id": "decision-1",
            "type": "decision",
            "data": {"config": {"condition": "persona_count > 10"}},
        }
        context = {
            "workflow_id": uuid4(),
            "project_id": uuid4(),
            "results": {
                "personas-1": {"persona_ids": ["id1", "id2", "id3"] * 5},  # 15 personas
            },
        }

        # Act
        result = await executor.execute(node, context)

        # Assert
        assert result["branch_taken"] == "true"
        assert result["result"] is True
        assert result["condition"] == "persona_count > 10"
        assert "evaluation_context" in result

    @pytest.mark.asyncio
    async def test_execute_false_condition(self, db_session: AsyncSession):
        """Test decision executor returns false branch when condition is false."""
        # Arrange
        executor = DecisionExecutor(db_session)

        node = {
            "id": "decision-1",
            "type": "decision",
            "data": {"config": {"condition": "persona_count > 10"}},
        }
        context = {
            "workflow_id": uuid4(),
            "project_id": uuid4(),
            "results": {
                "personas-1": {"persona_ids": ["id1", "id2"]},  # 2 personas
            },
        }

        # Act
        result = await executor.execute(node, context)

        # Assert
        assert result["branch_taken"] == "false"
        assert result["result"] is False

    @pytest.mark.asyncio
    async def test_execute_complex_and_condition(self, db_session: AsyncSession):
        """Test decision executor with complex AND condition."""
        # Arrange
        executor = DecisionExecutor(db_session)

        node = {
            "id": "decision-1",
            "type": "decision",
            "data": {
                "config": {
                    "condition": "persona_count > 10 and focus_group_status == 'completed'"
                }
            },
        }
        context = {
            "workflow_id": uuid4(),
            "project_id": uuid4(),
            "results": {
                "personas-1": {"persona_ids": ["id1"] * 15},  # 15 personas
                "focus-group-1": {
                    "focus_group_id": "fg-123",
                    "status": "completed",
                },
            },
        }

        # Act
        result = await executor.execute(node, context)

        # Assert
        assert result["branch_taken"] == "true"
        assert result["result"] is True

    @pytest.mark.asyncio
    async def test_execute_complex_or_condition(self, db_session: AsyncSession):
        """Test decision executor with complex OR condition."""
        # Arrange
        executor = DecisionExecutor(db_session)

        node = {
            "id": "decision-1",
            "type": "decision",
            "data": {
                "config": {"condition": "persona_count < 5 or survey_response_count > 20"}
            },
        }
        context = {
            "workflow_id": uuid4(),
            "project_id": uuid4(),
            "results": {
                "personas-1": {"persona_ids": ["id1"] * 10},  # 10 personas (not < 5)
                "survey-1": {
                    "survey_id": "survey-123",
                    "response_count": 25,  # > 20
                },
            },
        }

        # Act
        result = await executor.execute(node, context)

        # Assert
        assert result["branch_taken"] == "true"
        assert result["result"] is True

    @pytest.mark.asyncio
    async def test_execute_comparison_operators(self, db_session: AsyncSession):
        """Test decision executor with various comparison operators."""
        # Arrange
        executor = DecisionExecutor(db_session)

        context = {
            "workflow_id": uuid4(),
            "project_id": uuid4(),
            "results": {
                "personas-1": {"persona_ids": ["id1"] * 10},
            },
        }

        # Test ==
        node_eq = {
            "id": "decision-1",
            "type": "decision",
            "data": {"config": {"condition": "persona_count == 10"}},
        }
        result_eq = await executor.execute(node_eq, context)
        assert result_eq["branch_taken"] == "true"

        # Test !=
        node_ne = {
            "id": "decision-2",
            "type": "decision",
            "data": {"config": {"condition": "persona_count != 5"}},
        }
        result_ne = await executor.execute(node_ne, context)
        assert result_ne["branch_taken"] == "true"

        # Test >=
        node_ge = {
            "id": "decision-3",
            "type": "decision",
            "data": {"config": {"condition": "persona_count >= 10"}},
        }
        result_ge = await executor.execute(node_ge, context)
        assert result_ge["branch_taken"] == "true"

        # Test <=
        node_le = {
            "id": "decision-4",
            "type": "decision",
            "data": {"config": {"condition": "persona_count <= 10"}},
        }
        result_le = await executor.execute(node_le, context)
        assert result_le["branch_taken"] == "true"

    @pytest.mark.asyncio
    async def test_execute_uses_len_function(self, db_session: AsyncSession):
        """Test decision executor can use len() function (allowlisted)."""
        # Arrange
        executor = DecisionExecutor(db_session)

        node = {
            "id": "decision-1",
            "type": "decision",
            "data": {"config": {"condition": "len(personas) > 5"}},
        }
        context = {
            "workflow_id": uuid4(),
            "project_id": uuid4(),
            "results": {
                "personas-1": {"persona_ids": ["id1"] * 10},
            },
        }

        # Act
        result = await executor.execute(node, context)

        # Assert
        assert result["branch_taken"] == "true"

    @pytest.mark.asyncio
    async def test_execute_invalid_condition_syntax(self, db_session: AsyncSession):
        """Test decision executor raises error for invalid syntax."""
        # Arrange
        executor = DecisionExecutor(db_session)

        node = {
            "id": "decision-1",
            "type": "decision",
            "data": {"config": {"condition": "invalid_syntax =="}},  # Syntax error
        }
        context = {
            "workflow_id": uuid4(),
            "project_id": uuid4(),
            "results": {},
        }

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await executor.execute(node, context)

        assert "invalid condition" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_execute_missing_variable(self, db_session: AsyncSession):
        """Test decision executor raises error when condition references missing variable."""
        # Arrange
        executor = DecisionExecutor(db_session)

        node = {
            "id": "decision-1",
            "type": "decision",
            "data": {"config": {"condition": "missing_var > 10"}},
        }
        context = {
            "workflow_id": uuid4(),
            "project_id": uuid4(),
            "results": {},  # No missing_var
        }

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await executor.execute(node, context)

        assert "missing_var" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_execute_default_condition(self, db_session: AsyncSession):
        """Test decision executor uses default 'True' when condition is empty string."""
        # Arrange
        executor = DecisionExecutor(db_session)

        node = {
            "id": "decision-1",
            "type": "decision",
            "data": {"config": {"condition": ""}},  # Empty condition (will use 'True' default)
        }
        context = {
            "workflow_id": uuid4(),
            "project_id": uuid4(),
            "results": {},
        }

        # Act
        result = await executor.execute(node, context)

        # Assert - default is True
        assert result["branch_taken"] == "true"
        assert result["result"] is True

    @pytest.mark.asyncio
    async def test_execute_builds_correct_eval_context(self, db_session: AsyncSession):
        """Test decision executor builds correct evaluation context from results."""
        # Arrange
        executor = DecisionExecutor(db_session)

        node = {
            "id": "decision-1",
            "type": "decision",
            "data": {"config": {"condition": "True"}},
        }
        context = {
            "workflow_id": uuid4(),
            "project_id": uuid4(),
            "results": {
                "personas-1": {"persona_ids": ["id1", "id2"]},
                "focus-group-1": {
                    "focus_group_id": "fg-123",
                    "status": "completed",
                },
                "survey-1": {
                    "survey_id": "survey-123",
                    "response_count": 10,
                },
            },
        }

        # Act
        result = await executor.execute(node, context)

        # Assert - verify eval context contains extracted variables
        eval_context = result["evaluation_context"]
        assert "personas" in eval_context
        assert "persona_count" in eval_context
        assert eval_context["persona_count"] == 2
        assert "focus_group_id" in eval_context
        assert eval_context["focus_group_id"] == "fg-123"
        assert "focus_group_status" in eval_context
        assert eval_context["focus_group_status"] == "completed"
        assert "survey_id" in eval_context
        assert "survey_response_count" in eval_context
        assert eval_context["survey_response_count"] == 10

    @pytest.mark.asyncio
    async def test_execute_allowlisted_functions(self, db_session: AsyncSession):
        """Test decision executor allows safe builtin functions."""
        # Arrange
        executor = DecisionExecutor(db_session)

        context = {
            "workflow_id": uuid4(),
            "project_id": uuid4(),
            "results": {
                "personas-1": {"persona_ids": ["id1", "id2", "id3"]},
            },
        }

        # Test len()
        node_len = {
            "id": "decision-1",
            "type": "decision",
            "data": {"config": {"condition": "len(personas) == 3"}},
        }
        result_len = await executor.execute(node_len, context)
        assert result_len["branch_taken"] == "true"

        # Test bool()
        node_bool = {
            "id": "decision-2",
            "type": "decision",
            "data": {"config": {"condition": "bool(persona_count)"}},
        }
        result_bool = await executor.execute(node_bool, context)
        assert result_bool["branch_taken"] == "true"

        # Test int()
        node_int = {
            "id": "decision-3",
            "type": "decision",
            "data": {"config": {"condition": "int(persona_count) > 0"}},
        }
        result_int = await executor.execute(node_int, context)
        assert result_int["branch_taken"] == "true"

    @pytest.mark.asyncio
    async def test_execute_security_no_import(self, db_session: AsyncSession):
        """Test decision executor blocks __import__ for security."""
        # Arrange
        executor = DecisionExecutor(db_session)

        node = {
            "id": "decision-1",
            "type": "decision",
            "data": {"config": {"condition": "__import__('os').system('ls')"}},
        }
        context = {
            "workflow_id": uuid4(),
            "project_id": uuid4(),
            "results": {},
        }

        # Act & Assert
        with pytest.raises(ValueError):
            await executor.execute(node, context)

    @pytest.mark.asyncio
    async def test_execute_security_no_exec(self, db_session: AsyncSession):
        """Test decision executor blocks exec() for security."""
        # Arrange
        executor = DecisionExecutor(db_session)

        node = {
            "id": "decision-1",
            "type": "decision",
            "data": {"config": {"condition": "exec('print(1)')"}},
        }
        context = {
            "workflow_id": uuid4(),
            "project_id": uuid4(),
            "results": {},
        }

        # Act & Assert
        with pytest.raises(ValueError):
            await executor.execute(node, context)

    @pytest.mark.asyncio
    async def test_execute_security_no_open(self, db_session: AsyncSession):
        """Test decision executor blocks open() for security."""
        # Arrange
        executor = DecisionExecutor(db_session)

        node = {
            "id": "decision-1",
            "type": "decision",
            "data": {"config": {"condition": "open('/etc/passwd')"}},
        }
        context = {
            "workflow_id": uuid4(),
            "project_id": uuid4(),
            "results": {},
        }

        # Act & Assert
        with pytest.raises(ValueError):
            await executor.execute(node, context)

    @pytest.mark.asyncio
    async def test_execute_constants_available(self, db_session: AsyncSession):
        """Test decision executor has True, False, None constants available."""
        # Arrange
        executor = DecisionExecutor(db_session)

        context = {
            "workflow_id": uuid4(),
            "project_id": uuid4(),
            "results": {},
        }

        # Test True
        node_true = {
            "id": "decision-1",
            "type": "decision",
            "data": {"config": {"condition": "True"}},
        }
        result_true = await executor.execute(node_true, context)
        assert result_true["branch_taken"] == "true"

        # Test False
        node_false = {
            "id": "decision-2",
            "type": "decision",
            "data": {"config": {"condition": "False"}},
        }
        result_false = await executor.execute(node_false, context)
        assert result_false["branch_taken"] == "false"

        # Test None comparison
        node_none = {
            "id": "decision-3",
            "type": "decision",
            "data": {"config": {"condition": "None is None"}},
        }
        result_none = await executor.execute(node_none, context)
        assert result_none["branch_taken"] == "true"

    @pytest.mark.asyncio
    async def test_execute_with_empty_results(self, db_session: AsyncSession):
        """Test decision executor handles empty results context."""
        # Arrange
        executor = DecisionExecutor(db_session)

        node = {
            "id": "decision-1",
            "type": "decision",
            "data": {"config": {"condition": "True"}},
        }
        context = {
            "workflow_id": uuid4(),
            "project_id": uuid4(),
            "results": {},  # Empty results
        }

        # Act
        result = await executor.execute(node, context)

        # Assert - should still work with minimal context
        assert result["branch_taken"] == "true"

    @pytest.mark.asyncio
    async def test_execute_numeric_comparison(self, db_session: AsyncSession):
        """Test decision executor handles numeric comparisons correctly."""
        # Arrange
        executor = DecisionExecutor(db_session)

        node = {
            "id": "decision-1",
            "type": "decision",
            "data": {"config": {"condition": "persona_count >= 5 and persona_count <= 15"}},
        }
        context = {
            "workflow_id": uuid4(),
            "project_id": uuid4(),
            "results": {
                "personas-1": {"persona_ids": ["id1"] * 10},
            },
        }

        # Act
        result = await executor.execute(node, context)

        # Assert
        assert result["branch_taken"] == "true"
        assert result["result"] is True

    @pytest.mark.asyncio
    async def test_execute_string_comparison(self, db_session: AsyncSession):
        """Test decision executor handles string comparisons."""
        # Arrange
        executor = DecisionExecutor(db_session)

        node = {
            "id": "decision-1",
            "type": "decision",
            "data": {"config": {"condition": "focus_group_status == 'completed'"}},
        }
        context = {
            "workflow_id": uuid4(),
            "project_id": uuid4(),
            "results": {
                "focus-group-1": {
                    "focus_group_id": "fg-123",
                    "status": "completed",
                },
            },
        }

        # Act
        result = await executor.execute(node, context)

        # Assert
        assert result["branch_taken"] == "true"

    @pytest.mark.asyncio
    async def test_execute_not_operator(self, db_session: AsyncSession):
        """Test decision executor handles NOT operator."""
        # Arrange
        executor = DecisionExecutor(db_session)

        node = {
            "id": "decision-1",
            "type": "decision",
            "data": {"config": {"condition": "not persona_count < 5"}},
        }
        context = {
            "workflow_id": uuid4(),
            "project_id": uuid4(),
            "results": {
                "personas-1": {"persona_ids": ["id1"] * 10},  # 10 personas
            },
        }

        # Act
        result = await executor.execute(node, context)

        # Assert
        assert result["branch_taken"] == "true"

    @pytest.mark.asyncio
    async def test_execute_in_operator(self, db_session: AsyncSession):
        """Test decision executor handles IN operator with lists."""
        # Arrange
        executor = DecisionExecutor(db_session)

        node = {
            "id": "decision-1",
            "type": "decision",
            "data": {"config": {"condition": "focus_group_status in ['completed', 'running']"}},
        }
        context = {
            "workflow_id": uuid4(),
            "project_id": uuid4(),
            "results": {
                "focus-group-1": {
                    "focus_group_id": "fg-123",
                    "status": "completed",
                },
            },
        }

        # Act
        result = await executor.execute(node, context)

        # Assert
        assert result["branch_taken"] == "true"
